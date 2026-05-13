import base64
import re

parts = []
for i in range(5):
    with open(f'orcOS-source.tar.gz.b64.part{i}', 'rb') as f:
        parts.append(f.read())

data = b''.join(parts)
data_clean = re.sub(rb'[^A-Za-z0-9+/=]', b'', data)

# Corrige padding
missing = len(data_clean) % 4
if missing:
    data_clean += b'=' * (4 - missing)

with open('orcOS-source.tar.gz', 'wb') as f:
    f.write(base64.b64decode(data_clean))
print('Done!')
