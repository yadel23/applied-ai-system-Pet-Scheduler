# Reflection

I had very large expectations on implementing a RAG feature for my chatbot that can help users get quick answers on common pet care questions. I was very wrong at least with the current limitations i was facing. 
1. I faced many blockers on where to get data to feed my local llm. The best source i could find that was free was Wikipedia api. At first it seemed promising but it was difficult to extract the right articles to put together a comprehensive answer with limited resources.
2. Was facing either the wrong answer or was getting results that were very unexpected, ex. articles on animals as food not pets. 

Since this free resources the upside is that AI that was implemented in this project can't be misused. I have placed guardrails to help users with where in the step the AI failed and provided terminal feedback. The most surprising outcome is the ability for flan-t5-base a small local model to hallucinate and not provide the correct answers, both due to the lack in data and not always having the correct pulled data it often fails.  

Collaboration with Claude has been both helpful to plan and program. It has helped me better understand how to structure features and helped me implement the feature quickly. 