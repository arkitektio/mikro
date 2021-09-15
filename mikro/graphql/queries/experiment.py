from herre.wards.graphql import ParsedQuery


GET_EXPERIMENT = ParsedQuery("""
query Experiment($id: ID!){
  experiment(id: $id){
    id
    name
    description
    meta
  }
}
""")
