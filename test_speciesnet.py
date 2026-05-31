import json
import logging
import sys
from backend.services.species import SpeciesNetService

# Mock up a test to see if 'India' vs 'IN' makes a difference.
# Since we don't have the exact image path, we can just look up the documentation or test the behavior.
# Actually we can just run speciesnet directly or check if there is an error in its logs.

def test():
    try:
        from speciesnet import SpeciesNet, DEFAULT_MODEL
        sn = SpeciesNet(DEFAULT_MODEL)
        # Find an image to test on
        import glob
        images = glob.glob("c:/projects/WildWatch/app/src-tauri/icons/*.png")
        if not images:
            print("No images found for testing.")
            return

        test_img = images[0]
        
        print("Testing with country='India'")
        res1 = sn.predict(filepaths=[test_img], country="India")
        print(json.dumps(res1, indent=2))
        
        print("Testing with country='IN'")
        res2 = sn.predict(filepaths=[test_img], country="IN")
        print(json.dumps(res2, indent=2))
        
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test()
