from typing import List, Tuple

def simple_tokenize(text: str) -> List[str]:
    # lightweight tokenizer approximation (split on whitespace)
    return text.split()


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[Tuple[int,int,str]]:
    tokens = simple_tokenize(text)
    chunks = []
    i = 0
    n = len(tokens)
    while i < n:
        end = min(i + chunk_size, n)
        chunk_tokens = tokens[i:end]
        chunk_text = ' '.join(chunk_tokens)
        chunks.append((i, end, chunk_text))
        if end == n:
            break
        i = max(end - overlap, end)
    return chunks


if __name__ == '__main__':
    sample = ' '.join([f'word{i}' for i in range(1200)])
    ch = chunk_text(sample, chunk_size=500, overlap=100)
    print(f'created {len(ch)} chunks')
