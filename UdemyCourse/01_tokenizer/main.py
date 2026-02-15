import tiktoken

encoding = tiktoken.encoding_for_model("gpt-4o")

text = "Hello world I am Shubham Goel"
tokens = encoding.encode(text)
print(tokens)

de_tokens = encoding.decode(tokens)
print(de_tokens)