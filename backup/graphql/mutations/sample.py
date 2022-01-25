from herre.wards.graphql import ParsedQuery



CREATE_SAMPLE = ParsedQuery("""
mutation SampleCreate($name: String, $creator: String, $meta: GenericScalar, $experiments: [ID]) {
  createSample(name: $name, creator: $creator, meta: $meta, experiments: $experiments){
    id
    name
    creator {
        email
    }
  }
}
""")