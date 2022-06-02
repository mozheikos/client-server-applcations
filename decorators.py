import traceback

import pydantic
from log.logger import logger

def log(func):
    
    def wrapper(*args, **kwargs):
        exec_path, exec_func = traceback.format_stack(limit=2)[0].split('\n', 1)
        file_name, line_number, parent_func = [x.strip() for x in exec_path.split(', ')]
                
        logger.debug(
            '<{}> функция <{}> вызвана из {} ({}, {})'.format(
                    file_name.replace('File ', '').strip('"'),
                    func.__name__,
                    parent_func.replace('in ', ''),
                    exec_func.strip(),
                    line_number.replace('line', 'строка')
                )
            )
        
        try:
            result = func(*args, **kwargs)
        
        # Валидацию pydantic вынес отдельно, так как там немного другой строковый формат, чтоб лог не расползался
        except pydantic.ValidationError as e:
            e = ' '.join(list(map(lambda x: x.strip(), str(e).split('\n'))))
            logger.error("<{}> <{}>: {}".format(file_name.replace('File ', '').strip('"'), exec_func.strip(), e))
            return
            
        except Exception as e:
            logger.error("<{}> <{}>: {}".format(file_name.replace('File ', '').strip('"'), exec_func.strip(), e))    
            return
        else:
            return result
            
    return wrapper
