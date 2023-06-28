from the_history_atlas.api.resolvers import resolve_publish_new_citation


def test_resolve_publish_new_citation(info, writemodel_app):

    output = resolve_publish_new_citation(
        None,
        info,
    )
    assert output == writemodel_app.publish_citation.return_value
