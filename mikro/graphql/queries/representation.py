from herre.wards.graphql import ParsedQuery


FILTER_REPRESENTATION = ParsedQuery("""
query Representation($name: String) {
  representations(name: $name) {
    id
    name
    store
    variety
    tags
    unique
    creator {
      email
    }
    sample {
      id
    }
    meta
  }
}
""")

GET_REPRESENTATION = ParsedQuery("""
query Representation($id: ID!){
  representation(id: $id){
    id
    name
    tags
    variety
    store
    meta
    unique
    creator {
      email
    }
    sample {
      id
    }
  
  }
}
""")