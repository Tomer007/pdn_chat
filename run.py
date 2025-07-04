import app

app_instance = app.create_app()

if __name__ == '__main__':
    app_instance.run(debug=True, host='0.0.0.0', port=8001) 