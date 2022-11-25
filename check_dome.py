import subprocess
from datetime import datetime

from astropy.table import Table

FILE = "dome_info.csv"

EXPECT_SCRIPT = """
spawn telnet 199.17.126.17 2902
expect "'^]'."
sleep 1
send "?\r"
expect "D2"
"""

foo = subprocess.run("expect", input=EXPECT_SCRIPT, text=True, capture_output=True)
foo.stdout
now = datetime.now()

"spawn telnet 199.17.126.17 2902\nTrying 199.17.126.17...\n\nConnected to 199.17.126.17.\n\nEscape character is '^]'.\n\n?\nPosn 9.81\n[ON]\nRL 00 000\nD1 OPEN\nD2 OPEN\n>"

content = foo.stdout.split("\n\n?\n")[1].split("\n")[:-1]

position, who_knows, status, D1, D2 = content

bad_radio = status.endswith('RADIO')

status = status.split("RADIO")[0].strip() if bad_radio else status
position = float(position.split(" ")[1])
D1 = D1.split(" ")[1]
D2 = D2.split(" ")[1]

isodate = now.date().isoformat()
isotime = now.time().isoformat()
stamp = now.timestamp()
