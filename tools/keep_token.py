"""一次性：把 Google 登入後拿到的 oauth_token 換成 gkeepapi 用的 master token。
master token 等同帳號的長期登入憑證，只貼到 GitHub 的 Secrets，不要貼給任何人或聊天視窗。"""
import getpass
import gpsoauth

email = input("Google 帳號（完整信箱）：").strip()
oauth = getpass.getpass("oauth_token（貼上後按 Enter，畫面不會顯示）：").strip()
res = gpsoauth.exchange_token(email, oauth, "0123456789abcdef")
if "Token" in res:
    print("\nmaster token（存成 GitHub Secret：KEEP_MASTER_TOKEN）：\n" + res["Token"])
else:
    print("\n失敗：", res.get("Error", res))
