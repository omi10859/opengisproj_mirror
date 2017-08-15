import logging
from .models import *
import json
import shapefile
import os
def install(user):
    temp = options.objects.create(option_name="meta_field",value='{"key_name": "bod", "label": "BOD", "key_type": "number", "min": "", "max": "", "max_len": "", "step": "0.000001", "required": "True"}')
    temp.save()
    temp = options.objects.create(option_name="meta_field",value='{"key_name": "ph", "label": "ph Value", "key_type": "number", "min": "", "max": "", "max_len": "", "step": "0.00001", "required": "True"}')
    temp.save()
    temp = options.objects.create(option_name="meta_field",value='{"key_name": "longitude", "label": "Longitude", "key_type": "number", "min": "-180", "max": "180", "max_len": "", "step": "0.000001", "required": "True"}', is_removable=False)
    temp.save()
    temp = options.objects.create(option_name="meta_field",value='{"key_name": "latitude", "label": "Latitude", "key_type": "number", "min": "-90", "max": "90", "max_len": "", "step": "0.000001", "required": "True"}', is_removable=False)
    temp.save()
    temp = options.objects.create(option_name="meta_field",value='{"key_name": "year", "label": "Year", "key_type": "number", "min": "1947", "max": "2100", "max_len": "", "step": ""}', is_removable=False)
    temp.save()

def get_meta_fields(getjson=False):
    try:
        data = options.objects.filter(option_name="meta_field")
        jsonFields = []
        for d in data:
            temp = {}
            fields = json.loads(str(d.value))
            for x in fields:
                temp[x] = fields[x]
            temp["id"] = str(d.id)
            temp["is_removable"] = d.is_removable
            temp["data_group"] = str(d.data_group.id)
            jsonFields.append(temp)
        return jsonFields
    except Exception as e:
        toReturn = {}
        toReturn["status"] = "error"
        toReturn["msg"] = e
        toReturn["errcode"] = "500"
        return toReturn

def get_meta():
    try:
        gis_objects = gis_data.objects.all()    #Fetch all rows from gis_data
        arr = []    #Create a new array to return
        for x in gis_objects:
            obj = {}    #Create new empty dictionary
            gis_id = x.id
            obj["id"] = str(gis_id)  #Add Id to dictionary
            obj["data_group"] = str(x.data_group.id)
            gis_meta = gis_data_meta.objects.filter(data=gis_id)    #Fetch all rows from gis_data_meta that contain data for gis_id 
            for y in gis_meta:
                obj[y.key] = y.value    #Add Every Key to dictionary with it's value
            arr.append(obj)    #Add Current Dictionary to arr
        return arr  #return the final arr
    except Exception as e:
        toReturn = {}
        toReturn["status"] = "error"
        toReturn["msg"] = e
        toReturn["errcode"] = "500"
        return toReturn

def is_meta_key(key, data_group):
    try: 
        fields = get_meta_fields()
        flag = False
        for x in fields:
            print(x['data_group'])
            if x['key_name'] == key and str(x['data_group']) == data_group :
                flag = True
                break
        return flag
    except Exception as e:
        toReturn = {}
        toReturn["status"] = "error"
        toReturn["msg"] = e
        toReturn["errcode"] = "500"
        return toReturn

def add_new_data(post_data, request_user, ret_json=False):
    toReturn = {}
    try:
        is_first = True
        gis_id = -1
        group_id = data_groups.objects.filter(id=post_data["data_group"])
        if not group_id:
            return False
        group_id = group_id[0]
        for x in post_data:
            key = x
            val = post_data[key]
            if(is_meta_key(key, post_data["data_group"])):
                if(is_first):
                    g = gis_data.objects.create(created_by=request_user, data_group = group_id)
                    g.save()
                    gis_id = g
                    is_first=False
                m = gis_data_meta.objects.create(key=key, value=val, data=gis_id)
                m.save()
        if(ret_json):
            toReturn["status"] = "success"
            toReturn["id"] = gis_id.id
        else:
            return gis_id.id
    except Exception as e:
        toReturn["status"] = "error"
        print(e)
        toReturn["msg"] = e
        toReturn["errcode"] = "500"
    return toReturn
def get_data_groups():
    try:
        groups = data_groups.objects.all()
        arr = []
        for x in groups:
            obj = {}
            obj['id'] = x.id
            obj['name'] = x.name
            obj['is_removable'] = x.is_removable
            arr.append(obj)        
        return arr
    except Exception as e:
        return e

def add_param(data, user):
    toReturn = {}
    param = {}
    removable = False
    if(is_meta_key(data['key_name'],data['data_group'])):
        toReturn["status"] = "error"
        toReturn["message"] = "Key Already Exists"
        toReturn["errcode"] = "KEY_EXISTS"
    else:
        for x in data:
            key = x
            val = data[x]
            if x=="csrfmiddlewaretoken":
                continue
            if x=="required":
                val="True"
            if x=="is_removable":
                removable = True
                continue
            param[key] = val
        try:
            group_id = data_groups.objects.filter(id=data["data_group"])[0]
            jsonParam = json.dumps(param)
            p = options.objects.create(option_name="meta_field",value=jsonParam, is_removable = removable, data_group = group_id)
            p.save()
            toReturn["status"] = "success"
            toReturn["message"] = str(p.id)
        except Exception as e:
            toReturn["status"] = "error"
            toReturn["msg"] = "Some error"
            toReturn["errcode"] = "500"

    return toReturn

def remove_param(option_id, group_id, user):
    try:
        obj = options.objects.filter(id=option_id, data_group = group_id)
        toReturn = {}
        if not obj:
            toReturn['status'] = "error"
            toReturn['msg'] = "Option Id Not Found"
            toReturn['errcode'] = "OPTION_DOES_NOT_EXIST"
        else:
            if(obj[0].is_removable):
                fields = json.loads(str(obj[0].value))
                keyName = fields['key_name']
                gis_data_objects = gis_data.objects.filter(data_group = group_id)
                for gis_obj in gis_data_objects:
                    meta_rows = gis_data_meta.objects.filter(key=keyName, data=gis_obj)
                    meta_rows.delete()
                obj.delete()  
                toReturn['status'] = "success"
            else:
                toReturn['status'] = "error"
                toReturn['msg'] = "Option Cannot be Removed"
                toReturn['errcode'] = "OPTION_IS_NOT_REMOVABLE"
    except Exception as e:
        toReturn["status"] = "error"
        toReturn["msg"] = e
        toReturn["errcode"] = "500"

    return toReturn

def remove_gis_data(data_id, user):
    try:
        obj = gis_data.objects.filter(id=data_id)
        toReturn = {}
        if not obj:
            toReturn['status'] = "error"
            toReturn['msg'] = "Data Id Not Found"
            toReturn['errcode'] = "DATA_DOES_NOT_EXIST"
        else:
            obj_meta = gis_data_meta.objects.filter(data_id=data_id)
            obj_meta.delete()
            obj.delete()
            temp = gis_data.objects.filter(id=data_id)
            if not temp:
                toReturn['status'] = "success"
            else:
                toReturn['status'] = "error"
                toReturn['msg'] = "Internal Error"
                toReturn['errcode'] = "INTERNAL_ERROR"
    except Exception as e:
        toReturn["status"] = "error"
        toReturn["msg"] = e
        toReturn["errcode"] = "500"

    return toReturn

def edit_gis_data(meta_key, data_id, new_value, user):
    try:
        obj = gis_data_meta.objects.get(key=meta_key, data=data_id)
        toReturn = {}
        if not obj:
            toReturn['status'] = "error"
            toReturn['msg'] = "Data Id Not Found"
            toReturn['errcode'] = "DATA_DOES_NOT_EXIST"
        else:
            obj.value = new_value
            obj.save()
            toReturn['status'] = "success"
    except Exception as e:
        toReturn["status"] = "error"
        toReturn["msg"] = e
        toReturn["errcode"] = "500"

    return toReturn

def edit_gis_param(param_key, opt_id, new_value, user):
    toReturn = {}
    try:
        obj = options.objects.filter(id=opt_id)[0]
        jsonFields = []
        flag = False
        if param_key == 'is_removable':
            if new_value == "True":
                obj.is_removable = True
            else:
                obj.is_removable = False
            flag = True
        else:
            fields = json.loads(obj.value)
            for attr in fields:
                if(attr == param_key):
                    fields[attr] = new_value
                    flag = True
                    break
            if flag == False:
                fields[param_key] = new_value
            obj.value = json.dumps(fields)
        obj.save()
        toReturn['status'] = 'success'
    except Exception as e:
        toReturn["status"] = "error"
        toReturn["msg"] = e
        toReturn["errcode"] = "500"
    return toReturn

def add_data_group(data, user):
    toReturn = {}
    try:
        removable = False
        if 'is_removable' in data:
            removable = True
        group = data_groups.objects.create(name=data['group_name'],is_removable=removable)
        group.save()
        toReturn['status'] = "success"
        toReturn['message'] = group.id
    except Exception as e:
        toReturn["status"] = "error"
        toReturn["msg"] = e
        toReturn["errcode"] = "500"
    return toReturn

def remove_data_group(group_id, user):
    toReturn = {}
    try:
        obj = data_groups.objects.filter(id=group_id)
        toReturn = {}
        if not obj:
            toReturn['status'] = "error"
            toReturn['msg'] = "Group Id Not Found"
            toReturn['errcode'] = "GROUP_DOES_NOT_EXIST"
        else:
            obj = obj[0]
            if obj.is_removable == False:
                toReturn['status'] = "error"
                toReturn['msg'] = "Group Cannot be Deleted"
                toReturn['errcode'] = "GROUP_NOT_REMOVABLE"
            else:
                obj_data = gis_data.objects.filter(data_group=obj)
                for x in obj_data:
                    obj_meta = gis_data_meta.objects.filter(data=x)
                    obj_meta.delete()
                obj_data.delete()
                obj.delete()
                toReturn['status'] = "success"
    except Exception as e:
        toReturn["status"] = "error"
        toReturn["msg"] = e
        toReturn["errcode"] = "500"
    return toReturn
def edit_data_group(group_id, key, new_value, user):
    toReturn = {}
    try:
        obj = data_groups.objects.filter(id=group_id)[0]
        if key == "name":
            obj.name = new_value
        elif key == "is_removable":
            if(new_value == "False"):
                obj.is_removable = False
            else:
                obj.is_removable = True
        obj.save()
        toReturn["status"] = "success"
    except Exception as e:
        toReturn["status"] = "error"
        toReturn["msg"] = e
        toReturn["errcode"] = "500"
    return toReturn

def shapefile_reader():
    fileUrl = os.getcwd()+'\portal\static\portal\shapefiles\data1\lines'
    sf = shapefile.Reader(fileUrl)
    shapes = sf.shapes()
    data = []
    for x in range(len(shapes)):
        curr_shape = sf.shape(x)
        pairs = []
        for point in range(len(curr_shape.points)):
            pairs.append({"lat":curr_shape.points[point][1], "lng":curr_shape.points[point][0]})
        data.append(pairs)
    return data