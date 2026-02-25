import varlink
import os

def inspect_cosmic():
    socket_path = f"unix:/run/user/{os.getuid()}/cosmic-comp/com.system76.CosmicCompositor"
    try:
        with varlink.Client(socket_path) as client:
            interface = client.open("com.system76.CosmicCompositor")
            print("Interfaces:", client.get_interfaces())
            # We can't easily list methods without the varlink tool, 
            # but we can try common ones like ListViews
            print("Successfully connected to COSMIC Compositor.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_cosmic()
