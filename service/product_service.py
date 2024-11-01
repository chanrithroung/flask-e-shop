# def save(req, cur) -> bool:
#     cur.execute(f"INSERT INTO `category` (`name`) VALUE ({req['name']})")
    


save = lambda req, cur : cur.execute(f"INSERT INTO `category` (`name`) VALUE ({req['name']})")
