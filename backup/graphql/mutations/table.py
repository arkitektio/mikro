from herre.wards.graphql import ParsedQuery


CREATE_TABLE = ParsedQuery(
    """
mutation CreateTable($sample: ID, $name: String, $tags: [String], $creator: String, $representation: ID, $experiment: ID){
  createTable(sample: $sample, name: $name, representation: $representation, experiment: $experiment, tags: $tags, creator: $creator){
    name
    id
    tags
    store
  }
}
"""
)

UPDATE_TABLE = ParsedQuery(
    """
mutation UpdateTable($id: ID!){
  updateTable(id: $id){
    name
    id
    tags
    store
  }
}
"""
)
