from herre.wards.graphql import ParsedQuery

REP_FRAGMENT = """
  name
  id
  variety
  tags
  store
  unique
  meta
  omero {
    scale
    channels {
      name
    }
  }
  origins {
    id
    name
  }
"""


CREATE_REPRESENTATION = ParsedQuery(
    """
mutation Representation($sample: ID, $name: String, $tags: [String], $variety: RepresentationVarietyInput, $creator: String, $meta: GenericScalar, $omero: OmeroRepresentationInput, $origins: [ID]){
  createRepresentation(sample: $sample, name: $name, tags: $tags, variety: $variety, creator: $creator, meta: $meta, omero: $omero, origins: $origins){
    """
    + REP_FRAGMENT
    + """
  
  }
}
"""
)

UPDATE_REPRESENTATION = ParsedQuery(
    """
mutation Representation($id: ID!){
  updateRepresentation(rep: $id){
    """
    + REP_FRAGMENT
    + """

  }
}
"""
)
