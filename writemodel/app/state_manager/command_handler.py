"""Component responsible for validating Commands and emitting Events.

Friday, April 9th 2021
"""

import logging
from re import S
from uuid import uuid4

from .handler_errors import (CitationExistsError, UnknownCommandTypeError,
    CitationMissingFieldsError, GUIDError, UnknownTagTypeError)
from .event_composer import EventComposer

log = logging.getLogger(__name__)

TAG_TYPES = set(["PERSON", "PLACE", "TIME"])

class CommandHandler:
    """Class encapsulating logic to transform Commands from the user
    into canonical Events to be passed on to the Event Store."""

    def __init__(self, database_instance, hash_text):
        self._command_handlers = self._map_command_handlers()
        self._db = database_instance
        self._hashfunc = hash_text
 
    def handle_command(self, command: dict):
        """Receives a dict, processes it, and returns an Event
        or raises an Exception"""

        log.debug(f'handling command {command}')
        cmd_type = command.get('type')
        handler = self._command_handlers.get(cmd_type)
        if not handler:
            raise UnknownCommandTypeError
        event = handler(command)
        return event

    def _map_command_handlers(self):
        """Returns a dict of known commands mapping to their handle method."""
        return {
            'PUBLISH_NEW_CITATION': self._handle_publish_new_citation,
        }
        
    # command handlers

    def _handle_publish_new_citation(self, cmd):
        """Handles the PUBLISH_NEW_CITATION command.

        Validates the command's contents and returns a synthetic event 
        or raises an error.

        Raises a CitationMissingFieldsError if a field of the command 
            is not present.
        Raises a CitationExistsError error if text is not unique.
        Raises a GUIDError if any of the new GUIDs are not unique,
            or if any of the existing GUIDs don't match type.
        Raises a UnknownTagTypeError if an unknown tag is passed.
        """
        # a wrapper for handling new citations
        # provides a useful error if the command dict is missing fields
        try:
            return self.__handle_publish_new_citation(cmd)
        except KeyError as e:
            raise CitationMissingFieldsError(e)

    
    # utility methods

    def __handle_publish_new_citation(self, cmd):
        """logic for handle_publish_new_citations"""
        
        log.info(f'CommandHandler: received a new citation: {cmd}')
        # extract fields from command
        user = cmd['user']
        timestamp = cmd['timestamp']
        app_version = cmd['app_version']
        citation_GUID = cmd['payload']['GUID']
        tags = cmd['payload']['tags']
        meta = cmd['payload']['meta']
        summary = cmd['payload']['summary']
        summary_guid = summary['GUID']

        composer = EventComposer(
            transaction_guid=str(uuid4()),
            app_version=app_version,
            user=user,
            timestamp=timestamp)

        # validate that this text is unique
        text = cmd['payload']['text']
        hashed_text = self._hashfunc(text)
        log.debug(f'Text hash is {hashed_text}')
        if hash_guid := self._db.check_citation_for_uniqueness(hashed_text):
            log.info('tried (and failed) to publish duplicate citation')
            raise CitationExistsError(hash_guid)
        # add this to short term memory for preventing immediate duplication
        self._db.add_to_stm(key=hashed_text, value=citation_GUID)

        # check citation GUID
        if cit_res := self._db.check_guid_for_uniqueness(citation_GUID):
            raise GUIDError('Citation GUID was not unique. ' + \
                            f'Collided with GUID of type {cit_res}')
        # add this to short term memory for preventing immediate duplication
        self._db.add_to_stm(key=citation_GUID, value='CITATION')

        # check tag GUIDs. if they match, ensure that they are labeled correctly
        # tags will be added to composer by type during validation
        tag_guids = self.__parse_tags(tags, summary_guid, composer)

        # check meta GUID
        meta_guid = meta['GUID']
        if m_res := self._db.check_guid_for_uniqueness(meta_guid):
            if m_res != 'META':
                raise GUIDError(f'Meta GUID collided with GUID of type {m_res}')

        # add this to short term memory for preventing immediate duplication
        self._db.add_to_stm(key=meta_guid, value='META')        

        composer.make_META_ADDED(
            citation_guid=citation_GUID,
            meta_guid=meta_guid,
            author=meta['author'],
            publisher=meta['publisher'],
            title=meta['title'],
            # unpack remaining values after filtering for the ones we already have
            **{k:v 
                for k, v in meta.items()
                if k not in ('author', 'title', 'publisher', 'GUID')})

        composer.make_CITATION_ADDED(
            text=text,
            tags=tag_guids,
            meta=meta_guid,
            citation_guid=citation_GUID,
            summary_guid=summary_guid)

        # check summary guid
        if s_res := self._db.check_guid_for_uniqueness(summary_guid):
            if s_res != 'SUMMARY':
                raise GUIDError(f'Summary GUID collided with GUID of type {s_res}')
            # we're adding a new citation to this summary
            composer.make_SUMMARY_TAGGED(
                citation_guid=citation_GUID,
                summary_guid=summary_guid)
        else:
            # this is a new summary
            summary_text = summary['text']
            composer.make_SUMMARY_ADDED(
                citation_guid=citation_GUID,
                summary_guid=summary_guid,
                text=summary_text)
            self._db.add_to_stm(key=summary_guid, value='SUMMARY')

        return composer.events


    def __parse_tags(self,
        tags,
        summary_guid: str,
        composer: EventComposer
    ) -> list[str]:
        """Validates each tag's GUID and adds it to composer according to type."""

        tag_guids = []
        for tag in tags:
            t_guid = tag['GUID']
            t_type = tag['type']
            if t_type not in TAG_TYPES:
                raise UnknownTagTypeError(f'Tag of unknown type {t_type} was encountered')

            # check if tag already exists in the database
            if t_res := self._db.check_guid_for_uniqueness(t_guid):
                # and if it does, it must be the same type as this tag
                if t_type != t_res:
                    raise GUIDError(f'Tag GUID of type {t_type} doesn\'t match database type of {t_res}.')
                
                # make a tag of the correct type
                if t_type == 'PERSON':
                    log.debug(f'Tagging person {tag["name"]} of GUID {t_guid}')
                    composer.make_PERSON_TAGGED(
                        summary_guid=summary_guid,
                        person_guid=t_guid,
                        person_name=tag['name'],
                        citation_start=tag['start_char'],
                        citation_end=tag['stop_char'])
                elif t_type == 'PLACE':
                    log.debug(f'Tagging place {tag["name"]} of GUID {t_guid}')
                    composer.make_PLACE_TAGGED(
                        summary_guid=summary_guid,
                        place_guid=t_guid,
                        place_name=tag['name'],
                        citation_start=tag['start_char'],
                        citation_end=tag['stop_char'])
                elif t_type == 'TIME':
                    log.debug(f'Tagging time {tag["name"]} of GUID {t_guid}')
                    composer.make_TIME_TAGGED(
                        summary_guid=summary_guid,
                        time_guid=t_guid,
                        time_name=tag['name'],
                        citation_start=tag['start_char'],
                        citation_end=tag['stop_char'])       
                else:
                    raise Exception(f'Tag of unknown type {t_type} received - in tagged')
               
            # now we know our GUID is unique, so we need to construct a new tag
            else:

                # first add it to short term memory
                self._db.add_to_stm(key=t_guid, value=t_type)

                # make a tag of the correct type
                if t_type == 'PERSON':
                    log.debug(f'Adding person {tag["name"]} of GUID {t_guid}')
                    composer.make_PERSON_ADDED(
                        summary_guid=summary_guid,
                        person_guid=t_guid,
                        person_name=tag['name'],
                        citation_start=tag['start_char'],
                        citation_end=tag['stop_char'])
                elif t_type == 'PLACE':
                    log.debug(f'Adding place {tag["name"]} of GUID {t_guid}')
                    composer.make_PLACE_ADDED(
                        summary_guid=summary_guid,
                        place_guid=t_guid,
                        place_name=tag['name'],
                        citation_start=tag['start_char'],
                        citation_end=tag['stop_char'],
                        latitude=tag['latitude'],
                        longitude=tag['longitude'])
                elif t_type == 'TIME':
                    log.debug(f'Adding time {tag["name"]} of GUID {t_guid}')
                    composer.make_TIME_ADDED(
                        summary_guid=summary_guid,
                        time_guid=t_guid,
                        time_name=tag['name'],
                        citation_start=tag['start_char'],
                        citation_end=tag['stop_char'])
                else:
                    raise Exception(f'Tag of unknown type {t_type} received - in added') 
  
            log.debug(f'Successfully validated tag {tag}')
            tag_guids.append(t_guid)
        return tag_guids
