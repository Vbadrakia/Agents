import sys
from agents.knowledge_base import add_pdf, add_url, get_knowledge_stats

def main():
    print("🧠 AI Command Center - Knowledge Base Builder")
    print("---------------------------------------------")
    
    while True:
        print("\nOptions:")
        print("1. Add a PDF Book (.pdf)")
        print("2. Add a Web Article (URL)")
        print("3. View Knowledge Stats")
        print("4. Exit")
        
        choice = input("\nSelect an option (1-4): ")
        
        if choice == '1':
            path = input("Enter the full path to the PDF file (e.g., C:\\books\\trading.pdf):\n> ")
            print("Processing PDF... This may take a moment.")
            path = path.strip(' "\'') # Remove surrounding quotes if dragged into terminal
            result = add_pdf(path)
            print("\n" + result)
            
        elif choice == '2':
            url = input("Enter the URL (e.g., https://zerodha.com/...):\n> ")
            name = input("Enter a short name (optional, press Enter to skip):\n> ")
            print("Fetching and indexing...")
            result = add_url(url.strip(), name.strip() if name else None)
            print("\n" + result)
            
        elif choice == '3':
            stats = get_knowledge_stats()
            print("\n" + stats)
            
        elif choice == '4':
            print("Exiting...")
            break
        else:
            print("Invalid option.")

if __name__ == "__main__":
    main()
