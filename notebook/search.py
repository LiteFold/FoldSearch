from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()

completion = client.chat.completions.create(
    model="gpt-4o-search-preview",
    web_search_options={
        "search_context_size": "high",
    },
    messages=[
        {
            "role": "user",
            "content": "propose 5 novel compounds or ligands  that could treat a disease caused by over-expression of DENNDIA. Search papers and whatever possible resource which could be useful. And give the answer in json, with like compound name, their smiles, the reference paper etc",
        }
    ],
)

print(completion.choices[0].message.content)


