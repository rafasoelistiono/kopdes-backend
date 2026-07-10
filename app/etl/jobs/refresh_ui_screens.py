from app.repositories.ui_backup_repository import export_mapping_json_text, refresh_ui_backup


if __name__ == "__main__":
    result = refresh_ui_backup()
    print(result)
    print(export_mapping_json_text())
