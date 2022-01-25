from herre.wards.graphql import ParsedQuery


GET_SAMPLE = ParsedQuery("""
query Sample($id: ID!){
  sample(id: $id){
    id
    name
    meta
    experiments {
      id
    }
  }
}
""")


FILTER_SAMPLE = ParsedQuery("""
query Samples($creator: ID) {
  samples(creator: $creator) {
    name
    id
    representations {
        id
    }
    meta
    experiments {
      id
    }
  }
}
""")