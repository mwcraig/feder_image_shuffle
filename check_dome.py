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

try:
    foo = subprocess.run("expect", input=EXPECT_SCRIPT, text=True,
                         capture_output=True, timeout=10)
    mask = [False] * 10
except subprocess.TimeoutExpired:
    dome_data = ["NA"] * 8
    dome_data = [1, "NA", 0, "NA", 0, 0, "NA", "NA"]
    mask = [False, False] + [True] * 8
else:
    content = foo.stdout.split("\n?\n")[1].split("\n")[:-1]

    position, who_knows, status, D1, D2 = content

    bad_radio = 1 if status.endswith('RADIO') else 0

    status = status.split("RADIO")[0].strip() if bad_radio else status
    s1, s2, s3 = status.split(" ")
    pos_str, pos_angle = position.split(" ")
    pos_angle = float(pos_angle)
    D1 = D1.split(" ")[1]
    D2 = D2.split(" ")[1]

    dome_data = [bad_radio, pos_str, pos_angle, s1, s2, s3, D1, D2]

now = datetime.now()

# "spawn telnet 199.17.126.17 2902\nTrying 199.17.126.17...\n\nConnected to 199.17.126.17.\n\nEscape character is '^]'.\n\n?\nPosn 9.81\n[ON]\nRL 00 000\nD1 OPEN\nD2 OPEN\n>"



isodate = now.date().isoformat()
isotime = now.time().isoformat()
stamp = now.timestamp()

print(stamp)
#print(isodate, isotime, bad_radio, pos_str, pos_angle, s1, s2, s3, D1, D2)

try:
    data = Table.read(FILE)
    print(data['radio'].dtype)
except FileNotFoundError:
    names = ["date", "time", "radio", "pos string", "azimuth", "stat1", "stat2", "stat3", "D1", "D2"]
    data = Table(
        data=([isodate], [isotime], [bad_radio], [pos_str], [pos_angle], [s1], [s2], [s3], [D1], [D2]),
        names=names
    )
else:
    data.add_row([isodate, isotime] + dome_data, mask=mask)

print(data)

data.write(FILE, overwrite=True)