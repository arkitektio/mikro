try:
    from arkitekt.schema.widgets import SliderWidget, SearchWidget


    MY_TOP_REPRESENTATIONS = SearchWidget(query="""
                    query Search($search: String){
                        options: representations(name: $search){
                            value: id
                            label: name
                        }
                    }
                    """)


    MY_TOP_SAMPLES = SearchWidget(query="""
                    query Search($search: String){
                        options: samples(name: $search){
                            value: id
                            label: name
                        }
                    }
                    """)

except:
    MY_TOP_REPRESENTATIONS = None
    MY_TOP_SAMPLES = None