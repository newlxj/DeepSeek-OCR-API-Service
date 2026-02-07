
BASE_SIZE = 1024
IMAGE_SIZE = 768
CROP_MODE = True
MIN_CROPS= 2
MAX_CROPS= 6 # max:6
MAX_CONCURRENCY = 100 # If you have limited GPU memory, lower the concurrency count.
NUM_WORKERS = 64 # image pre-process (resize/padding) workers 
PRINT_NUM_VIS_TOKENS = False
SKIP_REPEAT = True
MODEL_PATH = '/mydisk/gpt/gptmodel/deepseek-ai/DeepSeek-OCR2' # change to your model path

# TODO: change INPUT_PATH
# .pdf: run_dpsk_ocr_pdf.py; 
# .jpg, .png, .jpeg: run_dpsk_ocr_image.py; 
# Omnidocbench images path: run_dpsk_ocr_eval_batch.py



INPUT_PATH = '/mydisk/zklz/deepseek-ocr/DeepSeek-OCR-2/DeepSeek-OCR2-master/DeepSeek-OCR2-vllm/高级市场管理 （练习题）.pdf'
OUTPUT_PATH = './outxxx'

PROMPT = '<image>\n<|grounding|>Convert the document to markdown.'
# PROMPT = '<image>\nFree OCR.'
# .......


from transformers import AutoTokenizer

TOKENIZER = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
