import os
import datetime

def knowledge_op(op, **kwargs):
    handler = KnowledgeHandler()
    if op == "read":
        return handler.read_file(kwargs.get("path"))
    elif op == "write":
        return handler.write_file(kwargs.get("path"), kwargs.get("content"))
    elif op == "sync_notebooklm":
        return handler.save_note(kwargs.get("title"), kwargs.get("content"))
    elif op == "list_notes":
        return handler.list_notes()
    else:
        return f"Error: Unknown operation '{op}'"

class KnowledgeHandler:
    def __init__(self):
        self.notes_dir = os.path.expanduser("~/Documents/WANDA_Notes")
        os.makedirs(self.notes_dir, exist_ok=True)

    def read_file(self, path):
        if not path or not os.path.exists(path):
            return f"Error: File not found at {path}"
        try:
            with open(path, "r") as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {e}"

    def write_file(self, path, content):
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(content)
            return f"Success: File written to {path}"
        except Exception as e:
            return f"Error writing file: {e}"

    def save_note(self, title, content):
        if not title:
            title = f"Note_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '_')]).rstrip()
        filename = safe_title.replace(' ', '_') + ".md"
        path = os.path.join(self.notes_dir, filename)
        
        try:
            with open(path, "w") as f:
                f.write(f"# {title}\n\n")
                f.write(f"Date: {datetime.datetime.now().isoformat()}\n")
                f.write("---\n\n")
                f.write(content)
            
            # Auto-sync to Google Drive
            sync_status = ""
            try:
                from wandavoice.skills.google_drive import GoogleDriveSkill
                from wandavoice.config import Config
                drive = GoogleDriveSkill(Config())
                sync_result = drive.upload_file(path)
                sync_status = f" | Drive: {sync_result}"
            except Exception as e:
                sync_status = f" | Drive Sync Failed: {e}"

            return f"Successfully synced: Note saved to {path}{sync_status}"
        except Exception as e:
            return f"Error saving note: {e}"

    def list_notes(self):
        try:
            files = [f for f in os.listdir(self.notes_dir) if f.endswith(".md")]
            if not files: return "No notes found."
            return "Found notes:\n" + "\n".join([f"- {f}" for f in files])
        except Exception as e:
            return f"Error listing notes: {e}"
