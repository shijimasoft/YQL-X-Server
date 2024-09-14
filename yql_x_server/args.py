import argparse
import os

module_dir = os.path.dirname(__file__)

# Args
parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, default=8000)
parser.add_argument("--host", type=str, default="0.0.0.0")
parser.add_argument("--owm_key", type=str, required=True)
parser.add_argument("--advert_link", type=str, default="https://yzu.moe", help="Link to provide for in app resources, default is my site :)")
args = parser.parse_args()