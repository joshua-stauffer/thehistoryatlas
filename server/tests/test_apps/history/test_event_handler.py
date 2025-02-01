from the_history_atlas.apps.domain.core import PersonInput


def test_create_person(readmodel_app, cleanup_tag) -> None:
    person = PersonInput(
        wikidata_id="Q1339",
        wikidata_url="https://www.wikidata.org/wiki/Q1339",
        name="Johann Sebastian Bach",
    )
    created_person = readmodel_app.create_person(person=person)
    cleanup_tag(created_person.id)
    assert created_person.id
    assert created_person.name == "Johann Sebastian Bach"
    assert created_person.wikidata_id == "Q1339"
    assert created_person.wikidata_url == "https://www.wikidata.org/wiki/Q1339"
