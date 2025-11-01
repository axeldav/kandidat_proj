# EUDAMED HELPER

AI workflow to for gaining insights into the eudamed database


## Workflow

1. User input
2. AI agent (ask followup questions)
    - There should be some criteria that the agent is trying to reach before being satisfied with questions
3. Agent fetch data via EUDAMED api
4. (Optional) Use RAG db from legal documentations for information retrieval if necessary
5. Return back answer to user with references to legal documentation.


## HOW TO RUN THE PROGRAM
Open mac terminal and type:

Prerequisites: 
- Put ´GEMINI_API_KEY´as variable in .zshrc file 

1. ```make activate```
2. ```make run```



## Other information
Good api that we could use for thesis case
https://github.com/openregulatory/eudamed-api

The records in EUDAMED includes these fields:
"basicUdi" : "XXXXXXXXXXXXX",
"primaryDi" : "XXXXXXXXXXXXX",

Since similar records from the same company have different basicUdi and different primaryDi it is more interesting to filter searches so that we dont have collections that share the same basicUdi.
