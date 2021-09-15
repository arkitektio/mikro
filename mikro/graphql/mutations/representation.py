from herre.wards.graphql import ParsedQuery


CREATE_REPRESENTATION = ParsedQuery("""
mutation Representation($sample: ID, $name: String, $tags: [String], $variety: RepresentationVarietyInput, $creator: String, $meta: GenericScalar){
  createRepresentation(sample: $sample, name: $name, tags: $tags, variety: $variety, creator: $creator, meta: $meta){
    name
    id
    variety
    tags
    store
    unique
    meta
  
  }
}
""")

UPDATE_REPRESENTATION = ParsedQuery("""
mutation Representation($id: ID!){
  updateRepresentation(rep: $id){
    name
    id
    variety
    tags
    store
    unique
    meta
  }
}
""")