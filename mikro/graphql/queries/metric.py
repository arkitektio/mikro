from herre.wards.graphql import ParsedQuery



GET_METRIC = ParsedQuery("""
query GetMetric($id: ID!){
  metric(id: $id){
    id
    rep {
      id
    }
    key
    value
    creator {
      id
    }
    createdAt
  }
}
""")