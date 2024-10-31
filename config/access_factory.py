from database.sql_db.dao.dao_user import get_all_menu_item_and_access_meta


# 本应用的权限工厂
class AccessFactory:
    # 读取数据库中配置的所有权限
    dict_label2menu_item_access_meta = get_all_menu_item_and_access_meta()

    # 基础默认权限，主页和个人中心
    default_menu_item_and_access_meta = (
        dict_label2menu_item_access_meta['个人信息页面'],
        dict_label2menu_item_access_meta['个人设置页面'],
        dict_label2menu_item_access_meta['工作台页面'],
    )
    # 团队管理员的默认权限，权限列表和用户权限
    group_admin_menu_item_and_access_meta = (
        dict_label2menu_item_access_meta['权限列表页面'],
        dict_label2menu_item_access_meta['用户授权页面'],
    )
    # 超级管理员的默认权限，权限列表和团队、角色、用户权限
    super_admin_menu_item_and_access_meta = (
        dict_label2menu_item_access_meta['权限列表页面'],
        dict_label2menu_item_access_meta['用户授权页面'],
        dict_label2menu_item_access_meta['团队管理页面'],
        dict_label2menu_item_access_meta['角色管理页面'],
    )
