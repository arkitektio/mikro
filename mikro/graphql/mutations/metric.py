from herre.wards.graphql import ParsedQuery


CREATE_METRIC = ParsedQuery("""
mutation CreateMetric($rep:ID!, $key: String!, $value: GenericScalar!){
  createMetric(rep: $rep, key: $key, value: $value){
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