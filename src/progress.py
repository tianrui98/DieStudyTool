"""
This module has three main functionalities:
1. Save intermediate result to a json file.
2. Read previous results into objects
3. Update the file structures according to matches

When are data saved? :
1. When user clicks "Save" button
2. When user moves to the next cluster/ stage

What data are saved & read? :
1. Current stage number & images checked
2. The current cluster address, list of identicals, set of matches, set of nomatches, best image address

When are data removed? :
1. When project is completed & excel file is exported
"""
#todo First compare image 1 against all others. Second, remove all matched images from the pool of comparisons. Third, move to the next (remaining) coin and repeat
#todo Discovered a flaw in step 2: All coins are compared to each other more than once. It should rather work like this: Step1: A is compared to B, C, and D. Step2: B is compared to  C and D. Step 3: C is compared to D. This simple model assumes that they are no matches. If, however, B is merged with C, the comparisons would be over.

#todo if A is compared with B (regardless of match), A should not be compared with B again.

import json
import os
import shutil
import glob
import pandas as pd
from src.objects import *
from src.root_logger import *
from datetime import datetime
from collections import defaultdict
import re
from pathlib import Path
def _serialize_identicals(identicals):
    res = []
    for s in identicals:
        res.append(list(s))
    return res

def _deserialize_identicals(identicals):
    res = []
    for l in identicals:
        res.append(set(l))
    return res

def _serialize_past_comparisons(past_comparisons):
    return {key : list(val) for key, val in past_comparisons.items() }

def _deserialize_past_comparisons(past_comparisons):
    d = {key : set(val) for key, val in past_comparisons.items() }
    return defaultdict(set, d)

def _collect_identicals(cluster):
    identical_group_list = []
    identical_name_list =[]
    for identical_set in sorted(cluster.identicals):
        identical_group_name = ""
        prev_type = ""
        for image_name in list(identical_set):
            image_id = image_name.split(".")[0] #without .jpg
            identical_name_list.append(image_id)
            curr_type, curr_name = image_id.split(";")
            if curr_type != prev_type:
                identical_group_name += image_id
            else:
                identical_group_name += str("_" + curr_name)
            prev_type = curr_type
        identical_group_list.append(identical_group_name)

    return identical_group_list, identical_name_list

def _concatenate_image_names(cluster):
    """get cluster name"""
    identical_group_list, identical_name_list = _collect_identicals(cluster)

    matches = []
    if cluster.best_image.id not in identical_name_list:
        matches.append(cluster.best_image.id)

    for image_name in sorted(cluster.matches):
        image_id = image_name.split(".")[0]
        if image_id not in identical_name_list:
            matches.append(image_id)

    final_names = identical_group_list + matches
    final_names = [n for n in final_names if not n == ""]
    new_cluster_name = "_".join(sorted(final_names))

    #max file name (255)
    if len(new_cluster_name) > 150:
        new_cluster_name = new_cluster_name[:147] + "_etc"
    return new_cluster_name

def _change_jpeg_to_jpg (project_folder):
    all_folders = [f for f in os.listdir(project_folder) if not f.startswith('.')]
    for folder_name in all_folders:
        all_images = os.listdir(str(project_folder + "/" + folder_name))
        for image_name in all_images:
            if ".jpeg" in image_name:
                new_name = image_name.split(".")[0] + ".jpg"
                os.rename(project_folder + "/" + folder_name + "/" + image_name, project_folder + "/" + folder_name + "/" + new_name)

def _change_name_in_past_comparisons (old_name, new_name, stage):
    if old_name in stage.past_comparisons:
        #change name in its counterpart's record
        for counterpart in stage.past_comparisons[old_name]:
            old_set = stage.past_comparisons.pop(counterpart)
            new_set = {e for e in old_set if e != old_name}
            new_set.add(new_name)
            stage.past_comparisons[counterpart] = new_set

        #change its own name
        old_set = stage.past_comparisons.pop(old_name)
        stage.past_comparisons[new_name] = old_set
    return stage

def _change_name_in_clusters_yet_to_check (old_name, new_name, stage):
    if old_name in stage.clusters_yet_to_check:
        stage.clusters_yet_to_check = {e for e in stage.clusters_yet_to_check if e != old_name}
        stage.clusters_yet_to_check.add(new_name)
    return stage

def _change_name_in_current_cluster(old_name, new_name, progress_data, project_folder, stage):
    if str(stage.stage_number) in progress_data[project_folder]["stages"] and old_name == progress_data[project_folder]["stages"][str(stage.stage_number)]["current_cluster"]:
        progress_data["current_cluster"] = new_name
    return progress_data

def start_new_project(original_project_address, project_name):
    """Create a new project. This will add a new hashmap to existing progress_data with the cluster information.
    The images with valid extensions under the original project folder will be copied into a new project folder within the program.
    All images under a cluster will be stored under "images"

    Args:
        original_project_address (str): the address of the chosen project folder
        project_name (str): the project name

    Returns:
        str, hashmap: new_project_folder, progress_data
    """
    #copy all images in the original folder to a new folder
    new_project_address =os.path.join(os.getcwd() ,"projects", project_name)
    os.makedirs(new_project_address)

    for folder_name in ("Singles", "Verified"):
        if not os.path.exists(os.path.join(new_project_address, folder_name)):
            os.mkdir(os.path.join(new_project_address, "Verified"))

    for file_extension in ("*.jpg", "*.jpeg", "*.png"):
        for file_path in glob.glob(os.path.join(original_project_address, '**', file_extension), recursive=True):
            new_path = os.path.join(new_project_address, os.path.basename(file_path))
            shutil.copy(file_path, new_path)

    #read existing progress data
    data_file = open("data.json", "r")
    progress_data = json.loads(data_file.read())
    progress_data[new_project_address] = {"clusters": {}, "stages": {}}

    #populate "cluster" with cluster information based on original project folders
    for cluster_name in os.listdir(original_project_address):
        if not cluster_name.startswith('.'):
            progress_data[new_project_address]["clusters"][cluster_name] = {
                "original_images": [f for f in os.listdir(os.path.join(original_project_address, cluster_name)) if not f.startswith(".")],
                "matches": [],
                "nomatches":[],
                "identicals":[],
                "best_image_name": ""}

    return new_project_address , progress_data

def create_new_stage_in_progress_data(progress_data, project_folder, stage):
    progress_data[project_folder]["stages"][str(stage.stage_number)] ={
        "clusters_yet_to_check": list(stage.clusters_yet_to_check)
        }
    return progress_data


def _create_cluster_info_dict (cluster):
    return {
    "original_images": list(cluster.matches),
    "identicals": _serialize_identicals(cluster.identicals),
    "matches": list(cluster.matches),
    "nomatches": list(cluster.nomatches),
    "best_image_name": cluster.best_image.name
    }

def _merge_singles(cluster, clusters_data, new_cluster_name):
    images_in_singles = set(clusters_data["Singles"]["matches"])
    for matched_single_name in cluster.matches:
        images_in_singles.remove(matched_single_name)
        new_cluster_name += "_" + matched_single_name.split(".")[0]
    if len(new_cluster_name) > 150:
        new_cluster_name = new_cluster_name[:147] + "_etc"
    clusters_data["Singles"]["matches"] = images_in_singles
    return clusters_data, new_cluster_name
def save_progress_data(project_folder, stage, cluster, progress_data):
    """
    Make changes to the progress data
    {"project_address" : {  "clusters": {cluster_name: {
                                                        "original_images": []
                                                        "identicals": [],
                                                        "matches": [],
                                                        "nomatches": []:
                                                        "best_image_name": [] :
                                                    }
                                            }
                            "stages": { 0: {
                                        "current_cluster" : ,
                                        "clusters_yet_to_check": [],
                                        "past_comparisons": {img_name : []} }}
    }

    *the update on "clusters" will only happen for stage 0, 3 and 4
    Return: progress_data
    """
    if str(stage.stage_number) not in progress_data[project_folder]["stages"]:
        progress_data = create_new_stage_in_progress_data(progress_data, project_folder, stage)

    clusters_data = progress_data[project_folder]["clusters"]
    #if Cluster is None (end of project) then do nothing
    if cluster:
        old_cluster_name = cluster.name
        new_cluster_name = None
        if stage.stage_number == 0:
            #move nomatches to singles cluster
            for image_name in cluster.nomatches:
                clusters_data["Singles"]["matches"].append(image_name)
            # if all images do not belong to the cluster -> delete the cluster
            if len(cluster.matches) == 0 and len(cluster.nomatches) > 0:
                best_image_name = clusters_data[old_cluster_name]["best_image_name"]
                clusters_data["Singles"]["matches"].append(best_image_name)
                clusters_data.pop(old_cluster_name)
                logger.debug(f"Removed cluster {cluster.name} from progress data")
            else:
                #delete old cluster name
                new_cluster_name = _concatenate_image_names(cluster)
                clusters_data.pop(old_cluster_name)
                clusters_data[new_cluster_name] = _create_cluster_info_dict(cluster)

        elif stage.stage_number == 1:
            #merge matched cluster with current cluster
            new_cluster_name = old_cluster_name
            for matched_cluster_name in cluster.matches:
                clusters_data[old_cluster_name]["matches"].extend(clusters_data[matched_cluster_name]["matches"])
                clusters_data.pop(matched_cluster_name)
                new_cluster_name += "_" + matched_cluster_name
            if len(new_cluster_name) > 150:
                new_cluster_name = new_cluster_name[:147] + "_etc"
            clusters_data[new_cluster_name] = clusters_data.pop(old_cluster_name)

        elif stage.stage_number == 2 :
            #merge matched singles with current cluster
            clusters_data, new_cluster_name = _merge_singles(cluster, clusters_data, old_cluster_name)
            #update matches with matched singles
            clusters_data[old_cluster_name]["matches"].extend(list(cluster.matches))
            clusters_data.pop(old_cluster_name)
            clusters_data[new_cluster_name] = clusters_data.pop(old_cluster_name)

        elif stage.stage_number == 3:
            clusters_data, new_cluster_name = _merge_singles(cluster, clusters_data, clusters_data[old_cluster_name]["best_image_name"])
            #create new cluster from matched singles
            matches = list(cluster.matches) + [cluster.best_image.name]
            clusters_data[new_cluster_name] = {
                "original_images": [],
                "identicals": [],
                "matches": matches,
                "nomatches": [],
                "best_image_name": cluster.best_image.name
            }

        elif stage.stage_number == 4:
            #overwrite only the identicals info
            clusters_data[cluster.name]["identicals"] = _serialize_identicals(cluster.identicals)

        if new_cluster_name:
            stage = _change_name_in_clusters_yet_to_check(old_cluster_name, new_cluster_name, stage)
            stage = _change_name_in_past_comparisons(old_cluster_name, new_cluster_name, stage)

        #update current cluster
        progress_data[project_folder]["stages"][str(stage.stage_number)]["current_cluster"] = new_cluster_name
        #update clusters_yet_to_check
        progress_data[project_folder]["stages"][str(stage.stage_number)]["clusters_yet_to_check"] = list(stage.clusters_yet_to_check)
        #update past_comparisons
        progress_data[project_folder]["stages"][str(stage.stage_number)]["past_comparisons"] = _serialize_past_comparisons(stage.past_comparisons)

    data_file = open("data.json", "w")
    json.dump(progress_data, data_file)
    data_file.close()
    logger.debug(f"Save progress data {progress_data}")

def clear_current_project(project_folder, progress_data):
    """remove current project from progress data & delete project folder
    """
    if project_folder in progress_data:
        _ = progress_data.pop(project_folder)
    data_file = open("data.json", "w")
    json.dump(progress_data, data_file)
    data_file.close()
    shutil.rmtree(project_folder)

def checkout_progress():
    """read json into dictionary
    """
    data_file = open("data.json", "r")
    progress_data = json.loads(data_file.read())
    return progress_data

def load_progress(project_folder, create_next_cluster = True, data_address = "data.json"):
    """read progress data and create objects"""
    app_folder = str(Path(__file__).resolve().parent.parent)
    if app_folder not in data_address:
        data_address_full = os.path.join(app_folder, data_address)
    else:
        data_address_full = data_address

    if app_folder not in project_folder:
        project_address_full = os.path.join(app_folder, project_folder)
    else:
        project_address_full = project_folder

    data_file = open(data_address_full, "r")
    progress_data = json.loads(data_file.read())
    #retrieve latest stage
    stage_number= max(progress_data[project_folder]["stages"].keys())
    stage_info = progress_data[project_folder]["stages"][stage_number]
    stage = Stage(int(stage_number), progress_data[project_folder])
    stage.clusters_yet_to_check = set(stage_info["clusters_yet_to_check"])
    stage.past_comparisons= _deserialize_past_comparisons(stage_info["past_comparisons"])
    #retrieve latest cluster
    current_cluster = stage_info["current_cluster"]
    if not create_next_cluster:
        return progress_data, stage, None
    if stage_number == "0":
        cluster_info = progress_data[project_folder]["clusters"][current_cluster]
        cluster = Cluster(cluster_info["cluster_address"], current_cluster,
        _deserialize_identicals(cluster_info["identicals"]),
        cluster_info["best_image_name"],
        set(cluster_info["matches"]),
        set(cluster_info["nomatches"]))
    else:
        if len(stage.clusters_yet_to_check) == 0:
            cluster = None
        elif current_cluster in stage.clusters_yet_to_check:
            cluster = _create_a_cluster(stage,project_address_full,current_cluster)
        # if current cluster has already been checked. give the next cluster in line
        else:
            next_in_line = list(stage.clusters_yet_to_check)[0]
            cluster = _create_a_cluster(stage, project_address_full, next_in_line)
            progress_data[project_folder]["stages"][str(stage.stage_number)]["current_cluster"] = cluster.name

    return progress_data, stage, cluster

def check_cluster_completion(cluster,stage):
    """Check if all images in the current cluster have all been processed
    Cluster == None is for situations where the completed cluster has only 1 image & get deleted
    """
    return cluster == None or (len(cluster.matches) + len(cluster.nomatches) + len(cluster.compared_before)== len(cluster.images) - 1)


def check_stage_completion(stage):
    #verified vs verified and single vs single stages are complete once there's only one cluster left
    if stage.stage_number == 1 or stage.stage_number == 3:
        return len(stage.clusters_yet_to_check) <=1
    else:
        return len(stage.clusters_yet_to_check) == 0

def check_project_completion(stage):
    return check_stage_completion(stage) and stage.stage_number == 4


def check_part1_completion(cluster,stage,project_folder):
    stage_completed = check_stage_completion(stage)
    is_third_stage = stage.stage_number >= 3
    case1 = stage_completed and is_third_stage

    #case2 we are at stage 1 and there is no singles in the folder
    singles_in_folder = [f for f in str(project_folder + "/Singles") if not f.startswith('.')]
    case2 = stage.stage_number == 1 and len(singles_in_folder) == 0

    #case3 we are at stage 2 or 3 and have matched all images (or all but one image) in "Singles" to the current cluster
    case3 = (stage.stage_number >= 2 and stage.stage_number < 4) and check_cluster_completion(cluster, stage) and len(cluster.nomatches) <= 1

    return case1 or case2 or case3

def mark_compared(left_name, right_name, stage):
    stage.past_comparisons[left_name].add(right_name)
    stage.past_comparisons[right_name].add(left_name)

    return stage

def unmark_compared(left_name, right_name, stage):
    stage.past_comparisons[left_name].remove(right_name)
    stage.past_comparisons[right_name].remove(left_name)
    return stage

def mark_cluster_completed(cluster, stage):
    """Remove current cluster name from clusters_yet_to_check. Before updating cluster name"""
    logger.debug(f"Mark cluster {cluster.name} complete")

    cluster_id = cluster.name.split(".")[0]
    if cluster_id in stage.clusters_yet_to_check:
        stage.clusters_yet_to_check.remove(cluster_id)
        logger.debug(f"Removed {cluster_id} off clusters_yet_to_check. Left with {stage.clusters_yet_to_check}")

    #Inspect Verified Stage and the rest: move the matched clusters off the yet_to_check list
    if stage.stage_number > 0 and stage.stage_number < 4:
        for image_name in list(cluster.matches):
            stage = mark_compared(cluster.best_image.name, image_name,stage)
            if image_name.split(".")[0] in stage.clusters_yet_to_check:
                stage.clusters_yet_to_check.remove(image_name.split(".")[0])
                logger.debug("Removed {} off clusters_yet_to_check".format(image_name.split(".")[0]))
        for image_name in list(cluster.nomatches):
            stage = mark_compared(cluster.best_image.name, image_name,stage)

    return stage

def unmark_cluster_completed(cluster,stage):
    """reverse marking cluster completed"""
    logger.debug("Undo Mark cluster complete")
    logger.debug(str(stage.clusters_yet_to_check))

    cluster_id = cluster.name.split(".")[0]
    if cluster_id not in stage.clusters_yet_to_check:
        stage.clusters_yet_to_check.add(cluster_id)
        logger.debug("Add {} back to clusters_yet_to_check".format(cluster_id))

    #Inspect Verified Stage and the rest: move the matched clusters off the yet_to_check list
    if stage.stage_number > 0 and stage.stage_number < 4:
        for image_name in list(cluster.matches):
            stage = unmark_compared(cluster.best_image.name, image_name,stage)
            if image_name.split(".")[0] not in stage.clusters_yet_to_check:
                stage.clusters_yet_to_check.add(image_name.split(".")[0])
                logger.debug("Add {} back to clusters_yet_to_check".format(image_name.split(".")[0]))
        for image_name in list(cluster.nomatches):
            stage = unmark_compared(cluster.best_image.name, image_name,stage)

    return stage

def copy_best_image_to_verified(cluster, project_folder):
    if not os.path.exists(project_folder + "/Verified"):
        os.mkdir(project_folder + "/Verified")
    old_image_address = cluster.address + "/" + cluster.best_image.name
    new_image_address = project_folder + "/Verified/" + cluster.name + ".jpg"
    shutil.copyfile(old_image_address, new_image_address)
    logger.debug("Copied best image of {} to Verified".format(cluster.name))
    return cluster


def _create_a_cluster(stage, clusters_data, next_cluster_name):
    if stage.stage_number == 0 :
        next_cluster = Cluster(cluster_name = next_cluster_name, images = clusters_data[next_cluster_name]["images"], identicals = [], best_image_name = None, matches = set(), nomatches = set())

    elif stage.stage_number == 1:
        next_cluster = Cluster(cluster_name = next_cluster_name, images = [v["best_image_name"] for k, v in clusters_data.items() if not k == "Singles"], identicals = [], best_image_name = clusters_data[next_cluster_name]["best_image_name"], matches = set(), nomatches = set())

        #replace the image's cluster name with the cluster it represents
        new_images_dict = {}

        for image_name in next_cluster.images_dict:
            new_image_obj = next_cluster.images_dict[image_name]
            new_image_obj.cluster = image_name.split(".")[0]
            new_images_dict[image_name] = new_image_obj

        next_cluster.images_dict = new_images_dict
        # next_cluster.images = _filter_compared_images(best_image_name_jpg, next_cluster.images,stage.past_comparisons)

    elif stage.stage_number == 2:
        #A cluster should include all images in the Singles folder + best_image from one of the Verified. Cluster named after verified
        # TODO disable "Best_image"
        best_image_name = next_cluster_name
        best_image_name_jpg = best_image_name +".jpg"
        best_image_address = project_folder + "/Verified/" + best_image_name_jpg
        next_cluster = Cluster(str(project_folder +"/Singles"), cluster_name = next_cluster_name, identicals = [], matches = set(), nomatches = set())
        #replace the image's cluster name with the cluster it represents
        new_images_dict = {}
        for image_name in next_cluster.images_dict:
            new_image_obj = next_cluster.images_dict[image_name]
            new_image_obj.cluster = "Singles"
            new_images_dict[image_name] = new_image_obj

        next_cluster.images_dict = new_images_dict

        #set the best image
        best_image_obj = ImgObj(best_image_address, best_image_name)
        next_cluster.images_dict[best_image_name] = best_image_obj
        next_cluster.images = [best_image_obj] + next_cluster.images
        next_cluster.best_image = best_image_obj

    elif stage.stage_number == 3:
        #A cluster should include all images in the Singles folder, except those have been matched

        best_image_name_jpg = next_cluster_name+".jpg"
        best_image_address = project_folder + "/Singles/" + best_image_name_jpg

        next_cluster = Cluster(str(project_folder +"/Singles"), cluster_name = next_cluster_name, identicals = [], best_image_name = best_image_name_jpg, matches = set(), nomatches = set())
        #replace the image's cluster name with Singles
        new_images_dict = {}
        for image_name in next_cluster.images_dict:
            new_image_obj = next_cluster.images_dict[image_name]
            new_image_obj.cluster = "Singles"
            new_images_dict[image_name] = new_image_obj

        next_cluster.images_dict = new_images_dict

    else:
        next_cluster = Cluster(str(project_folder +"/"+next_cluster_name), cluster_name = next_cluster_name, identicals = [], best_image_name = None, matches = set(), nomatches = set())
        #at stage 4, all images in the cluster folder have been marked as matches
        next_cluster.matches = {obj.name for obj in next_cluster.images[1:]}

    return next_cluster

def create_next_cluster(stage, project_folder):
    """If the new cluster has only 1 image. the interface will take care of it"""
    if len(stage.clusters_yet_to_check) == 0:
        logger.error(f"stage {stage.stage_number} clusters yet to check is zero")
        return None

    next_cluster_name = list(stage.clusters_yet_to_check)[0]
    logger.debug("Create next cluster {}".format(next_cluster_name))
    next_cluster = _create_a_cluster(stage, project_folder, next_cluster_name)
    return next_cluster


def create_next_stage( stage, project_folder):
    new_stage = Stage(stage.stage_number+1, project_folder)
    logger.debug(f"Next stage {new_stage.name}. yet to check: {new_stage.clusters_yet_to_check}")
    new_cluster = create_next_cluster(new_stage, project_folder)

    return new_cluster, new_stage

def create_find_identical_stage(project_folder):
    new_stage = Stage(4, project_folder)
    logger.debug(f"Next stage {new_stage.name}. yet to check: {new_stage.clusters_yet_to_check}")
    new_cluster = create_next_cluster(new_stage, project_folder)

    return new_cluster, new_stage

def _concatenate_identical_set(identical_set):
    identical_group_name = ""
    prev_type = ""

    for image_name in sorted(identical_set):
        image_id = image_name.split(".")[0] #without .jpg
        curr_type, curr_name = image_id.split(";")
        if curr_type != prev_type:
            identical_group_name += image_id
        else:
            identical_group_name += str("_" + curr_name)
        prev_type = curr_type
    return str("(" + identical_group_name +")")

def _concatenate_identicals(identicals):
    final_name = ""
    number_to_deduct = 0
    for identical_set in sorted(identicals):
        final_name += _concatenate_identical_set(identical_set)
        number_to_deduct += len(identical_set) - 1
    return final_name, number_to_deduct

def export_results(project_folder, progress_data, save_address, keep_progress):
    """Generate excel sheet & move cluster out & wipe out progress data"""

    #write none-single clusters
    clusters = progress_data[project_folder]["clusters"]
    max_length = 0
    total_number = 0
    for _, cluster in clusters.items():
        max_length = max(max_length, 1 + len(cluster["matches"]))

    #TODO: put single coins into the matches of the "Singlee" cluster

    columns = list(range(1, max_length + 1)) + ["Identical", "Num"]
    data = []
    for cluster_name, cluster in clusters.items():
        if cluster_name != "Singles":
            all_images = cluster["matches"] + [cluster["best_image_name"]]
            all_images = sorted(list(all_images))
            data_row = all_images + [""] * (max_length - len(all_images))
            identicals = cluster["identicals"]
            final_name, number_to_deduct = _concatenate_identicals(identicals)
            data_row.append(final_name)
            data_row.append(str(len(all_images) - number_to_deduct))
            total_number += len(all_images) - number_to_deduct
            data.append(data_row)

    #write "Singles" cluster
    all_singles = set([f for f in os.listdir(str(project_folder + "/Singles")) if not f.startswith('.')])
    identicals = progress_data[project_folder]["clusters"]["Singles"]["identicals"]
    singles_seen = set()
    for identical_set in identicals:
        all_images = sorted(list(identical_set))
        data_row = all_images + [""] * (max_length - len(all_images))
        identical_final_name = _concatenate_identical_set(identical_set)
        data_row.append(identical_final_name)
        data_row.append("1")
        total_number += 1
        data.append(data_row)
        singles_seen = set.union(singles_seen, identical_set)

    for single_jpg in all_singles:
        single_id = single_jpg.split(".")[0]
        if single_jpg not in singles_seen:
            data_row = [single_id] + [""] * (max_length - 1)
            data_row.append("")
            data_row.append(str(1))
            data.append(data_row)
            total_number += 1

    data.append([""] * max_length +["sum"] + [str(total_number)])
    res = pd.DataFrame(data, columns=columns)
    res = res.applymap(lambda x : x.split('.')[0])

    project_folder_name = project_folder.split("/")[-1] + "_" + str(datetime.now().strftime('%Y-%m-%d-%H-%M'))

    if keep_progress:
        shutil.copytree(project_folder, save_address + "/" + project_folder_name )
        res.to_excel(save_address + "/" + project_folder_name + "/" + "results_" + project_folder_name + ".xlsx", index= False)
    else:
        #move folders
        shutil.move(project_folder, save_address + "/" + project_folder_name )
        res.to_excel(save_address + "/" + project_folder_name + "/" + "results_" + project_folder_name + ".xlsx", index= False)

        #wipe out the records in progress data
        _  = progress_data.pop(project_folder)

        data_file = open("data.json", "w")
        json.dump(progress_data, data_file)
        data_file.close()
    return res


def check_completion_and_save(cluster, stage, project_folder, progress_data):
    """
    Saves current data to data.json and creates new cluster or stage
    This function is called when user clicks "save" or "exit"
    Called after "update_folder_and_record" is done
    """

    # save_progress_data(project_folder,stage,cluster,progress_data)

    # new_progress_data = checkout_progress()
    new_progress_data = progress_data
    #create new cluster or stage
    if check_project_completion(stage):
        save_progress_data(project_folder,stage,cluster,progress_data)
    elif check_part1_completion(cluster,stage,project_folder):
        new_cluster, new_stage = create_find_identical_stage(project_folder)
        save_progress_data(project_folder,new_stage, new_cluster, new_progress_data)
    else:
        if check_stage_completion(stage):
            new_cluster, new_stage = create_next_stage(stage, project_folder)
            while not new_cluster:
                logger.debug(f"Skip stage {new_stage.name}")
                new_cluster, new_stage = create_next_stage(new_stage,project_folder)
            save_progress_data(project_folder,new_stage, new_cluster, new_progress_data)    
        else:
            if check_cluster_completion(cluster, stage):
                new_cluster = create_next_cluster(stage, project_folder)
                #if the "Singles" cluster has no images, skip to the next
                if len(new_cluster.images) == 0:
                    logger.debug(f"Skip cluster {new_cluster.name}")
                    stage = mark_cluster_completed(new_cluster, stage)
                    check_completion_and_save(new_cluster, stage, project_folder, progress_data )
                save_progress_data(project_folder,stage, new_cluster, new_progress_data)