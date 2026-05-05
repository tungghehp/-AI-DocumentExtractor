from datetime import datetime

test = "10/02/2026"
dt = datetime.strptime(test, "%d/%m/%Y")
print(dt)