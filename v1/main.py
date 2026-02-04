from extractor import extract_entities
from ir_builder import build_ir
from compiler import compile_mysql


def run():
    print("English to SQL (Level 1)")
    print("Type 'exit' to quit\n")

    while True:
        query = input(">> ")

        if query.lower() == "exit":
            break

        try:
            parsed = extract_entities(query)
            ir = build_ir(parsed)
            sql = compile_mysql(ir)

            print("\nGenerated SQL:")
            print(sql)
            print()

        except Exception as e:
            print("Error:", e)


if __name__ == "__main__":
    run()