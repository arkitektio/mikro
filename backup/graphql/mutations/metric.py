from herre.wards.graphql import ParsedQuery


CREATE_METRIC = ParsedQuery(
    """
mutation CreateMetric($rep:ID, $sample: ID, $experiment: ID, $key: String!, $value: GenericScalar!){
  createMetric(rep: $rep,sample: $sample,experiment: $experiment, key: $key, value: $value){
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
"""
)
