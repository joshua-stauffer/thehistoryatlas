events.append(
    WikiEvent(
        summary=summary,
        people_tags=people_tags,
        place_tag=place_tag,
        time_tag=time_tag,
        entity_id=self._entity_id,
        secondary_entity_id=employer_id,
        context={
            **self._create_base_context(),
            "person_name": person_name,
            "employer": {"id": employer_id, "name": place_name},
            "position": (
                {"id": position_id, "name": position_name} if position_id else None
            ),
            "start_date": time_definition.model_dump(),
            "employment_claim": claim,
        },
    )
)
