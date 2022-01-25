from herre.wards.graphql import ParsedQuery


GET_TABLE = ParsedQuery(
    """
query Table($id: ID!){
  table(id: $id){
    id
    name
    tags
    store
    creator {
      email
    }
    sample {
      id
    }
    representation {
      id
    }
    experiment {
      id
    }
  
  }
}
"""
)
