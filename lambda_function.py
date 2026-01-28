import json
import os
import re
from datetime import datetime
from enum import Enum
import boto3
import utils.log_util as log


class LanguageIdentificationType(Enum):
    """言語識別タイプ"""
    SPECIFIC_LANGUAGE = "特定言語"              # 特定言語（LanguageCode指定）
    SINGLE_LANGUAGE_AUTO = "単一言語自動識別"    # 単一言語自動識別（IdentifyLanguage=True）
    MULTI_LANGUAGE_AUTO = "複数言語自動識別"     # 複数言語自動識別（IdentifyMultipleLanguages=True）


# todo 通过数据库获取
input_from_db = {
    "ファイル名": "v_12345678_202601221204123.mp4",
    "識別タイプ": "複数言語自動識別",
    "言語オプション": "ja-JP,zh-CN,en-IE",
    "prompt番号": "0001",
    "Temperature": "0.9",
    "TopP": "0.999",
    "TopK": "250"
}

def load_config():
    phase = os.environ.get('phase', 'UT')
    log.info('Current phase', phase=phase)

    config_path = os.path.join(os.path.dirname(__file__), 'conf', f'conf_{phase}.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_work_info(object_key):
    """
    从object key中提取media_type、work_id和datetime
    例如: auto_translate/v_12345678_202601221204123.mp4
    返回: media_type=v, work_id=12345678, datetime=202601221204123
    """
    filename = os.path.basename(object_key)
    pattern = r'([a-zA-Z]+)_(\d+)_(\d+)'
    match = re.search(pattern, filename)

    if match:
        return {
            'media_type': match.group(1),
            'work_id': match.group(2),
            'datetime': match.group(3)
        }
    return None

def validate_filename(object_key, db_input):
    """
    验证event中的文件名与数据库中的是否一致
    """
    event_filename = os.path.basename(object_key)
    db_filename = db_input["ファイル名"]

    if event_filename != db_filename:
        log.error('Filename mismatch', event_filename=event_filename, db_filename=db_filename)
        return False
    return True


def start_transcription(source_bucket, object_key, work_info, config, db_input):
    """
    启动AWS Transcribe转录任务
    根据db_input中的識別タイプ配置语言识别方式
    """
    transcribe_client = boto3.client('transcribe')
    transcribe_config = config['transcribe']

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S') + datetime.now().strftime('%f')[:3]
    job_name = f"auto_tslt_{work_info['work_id']}_{timestamp}"
    media_uri = f"s3://{source_bucket}/{object_key}"
    output_key = f"{transcribe_config['output_prefix']}{work_info['work_id']}_{work_info['datetime']}"

    # 基础参数
    job_params = {
        'TranscriptionJobName': job_name,
        'Media': {'MediaFileUri': media_uri},
        'MediaFormat': transcribe_config['media_format'],
        'OutputBucketName': transcribe_config['output_bucket'],
        'OutputKey': output_key,
        'Subtitles': {
            'Formats': transcribe_config['subtitle_formats'],
            'OutputStartIndex': 1
        }
    }

    # 根据識別タイプ配置语言参数
    identification_type = db_input["識別タイプ"]
    language_options_str = db_input.get("言語オプション", "")  # 逗号分隔的字符串

    # 解析逗号分隔的字符串为数组，传给Transcribe API
    language_options = [lang.strip() for lang in language_options_str.split(",") if lang.strip()] if language_options_str else []

    if identification_type == LanguageIdentificationType.SPECIFIC_LANGUAGE.value:
        # 特定言語：必须设置一个语言
        if not language_options or len(language_options) == 0:
            log.error('Specific language requires exactly one language option')
            raise ValueError("特定言語 requires exactly one language in 言語オプション")
        job_params['LanguageCode'] = language_options[0]
        log.info('Using specific language', language_code=language_options[0])

    elif identification_type == LanguageIdentificationType.SINGLE_LANGUAGE_AUTO.value:
        # 単一言語自動識別
        job_params['IdentifyLanguage'] = True
        # 当言語オプション有值时才指定
        if language_options:
            job_params['LanguageOptions'] = language_options
            log.info('Using single language auto identification', language_options=language_options_str)
        else:
            log.info('Using single language auto identification without language options')

    elif identification_type == LanguageIdentificationType.MULTI_LANGUAGE_AUTO.value:
        # 複数言語自動識別
        job_params['IdentifyMultipleLanguages'] = True
        # 当言語オプション有值时才指定
        if language_options:
            job_params['LanguageOptions'] = language_options
            log.info('Using multi language auto identification', language_options=language_options_str)
        else:
            log.info('Using multi language auto identification without language options')

    else:
        # 未知的識別タイプ
        log.error('Unknown identification type', identification_type=identification_type)
        raise ValueError(f"Unknown identification type: {identification_type}")
    
    log.info('Starting transcription job', job_params=job_params)

    response = transcribe_client.start_transcription_job(**job_params)

    return response

def lambda_handler(event, context):
    config = load_config()

    log.begin('lambda_handler')
    log.info('Received event', event=event)
    log.info('Loaded config', config=config)

    # 从事件中提取S3信息
    source_bucket = event['detail']['bucket']['name']
    object_key = event['detail']['object']['key']

    log.info('S3 info', source_bucket=source_bucket, object_key=object_key)

    # 验证文件名是否与数据库一致
    if not validate_filename(object_key, input_from_db):
        return {
            'statusCode': 400,
            'body': json.dumps('Filename mismatch between event and database')
        }

    # 提取work_id和datetime
    work_info = extract_work_info(object_key)

    if not work_info:
        log.error('Failed to extract work info', object_key=object_key)
        return {
            'statusCode': 400,
            'body': json.dumps('Invalid object key format')
        }

    log.info('Extracted work info', work_id=work_info['work_id'], datetime=work_info['datetime'])

    # 启动Transcribe任务
    transcribe_response = start_transcription(source_bucket, object_key, work_info, config, input_from_db)
    log.info('Transcribe job started', job_name=transcribe_response['TranscriptionJob']['TranscriptionJobName'])
    log.end('lambda_handler')

    log.info('transcribe_response', response=transcribe_response)

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Transcription job started',
            'work_id': work_info['work_id'],
            'datetime': work_info['datetime'],
            'job_name': transcribe_response['TranscriptionJob']['TranscriptionJobName']
        })
    }
