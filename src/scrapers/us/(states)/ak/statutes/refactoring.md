# Alaska Statutes

## General Notes
readAK.py is NOT used in this jurisdiction.
processAK is only used for GENERIC processing and can be nuked.

Alaska is an incredibly complex state website. It is incredibly old. Because dynamically loaded javascript is needed, which loads the addendum sidebar, Selenium is the best choice for this state. There are some inherent complexity with using Selenium, which makes Alaska one of the SLOWEST states to scrape. 

References are done weird, they show up in the sidebar.
- More work needs to be done on understanding references
- How to extract paragraph_id of references (next character after href text is most likely '(a)')

NodeText is currently impossible to determine the hierarchical nature. Possible solutions include the filtering of ```html &nbps; ```, which denotes the indentation level. Although, indendation level alone can NOT 100% indicate child/parent relationships. Could be a start though.



## Refactoring Checklist
- [x] Standardize Helper Functions
- [x] Rework Pydantic Model Usage
- [x] Ensure Consistent Variable Naming, Typing, and Documentation

## Previous Refactoring Work Done
1. Basic refactoring:
- Standardize Helper Functions
- Rework using Pydantic Model
- Consistent naming, typing, documentation


## Future Refactoring Work Needed
1. Extensively test initial refactoring
2. Improve Selenium time efficiency
3. Research and better understand addendum references (currently stored in core_metadata)
4. Try researching a system for tagging paragraphs that contain terms/definitions

