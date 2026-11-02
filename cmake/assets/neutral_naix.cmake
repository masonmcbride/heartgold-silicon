# Original versioned Pokédex archive recipes: sed 's/_gold//g'. Only names change, never IDs.
file(READ "${INPUT}" contents)
string(REPLACE "_gold" "" contents "${contents}")
file(WRITE "${OUTPUT}" "${contents}")
