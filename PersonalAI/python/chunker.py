"""Simple text chunker utility.
Splits on words and creates overlapping chunks of approximate size.
"""
def chunk_text(text, chunk_words=200, overlap=50):
    words = text.split()
    chunks = []
    i = 0
    n = len(words)
    while i < n:
        end = min(i + chunk_words, n)
        chunk = " ".join(words[i:end])
        chunks.append(chunk)
        if end == n:
            break
        i = end - overlap
    return chunks

if __name__ == '__main__':
    import sys
    txt = open(sys.argv[1], 'r', encoding='utf-8').read()
    for i,c in enumerate(chunk_text(txt, 100, 20)):
        print(f"--- CHUNK {i} ---\n{c}\n")
