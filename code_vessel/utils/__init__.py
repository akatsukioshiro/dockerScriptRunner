import appdirs

def get_app_location():
    app_name   = "code_vessel"
    app_author = "ashish"
    return appdirs.user_data_dir(app_name, app_author)
