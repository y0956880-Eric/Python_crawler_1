from playwright.sync_api import sync_playwright
 
def main():
    with sync_playwright() as p:
        print("建立資源檔")
    print("釋放資源檔")

if __name__ =="__main__":
    main()