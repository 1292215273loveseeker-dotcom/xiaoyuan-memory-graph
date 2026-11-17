import relate

print("version:", relate.__version__)
conn = relate.connect(":memory:")
row = conn.execute("RETURN 'ok' AS status").single()
print("row:", row)
conn.close()
