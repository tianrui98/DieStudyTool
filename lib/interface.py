import shutil
import tkinter as tk
from tkinter.constants import CENTER, RAISED, RIDGE
from PIL import Image, ImageTk
import math
from tkinter import Toplevel, filedialog
from tkinter.filedialog import askopenfile
import os
from objects import *
import progress
import shutil
from root_logger import *
#%% UI
class MainUI:
    def __init__(self):
        # main interface
        self.root = tk.Tk()
        self.root.title("Die Study Tool")
        self.project_name = ""
        self.project_address = ""
        self.progress_data = {}
        self.root.geometry("1300x850")
        self.root.minsize(width=1300, height=850)
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)
        self.root.columnconfigure(2, weight=1)
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=2)
        self.root.rowconfigure(2, weight=0)
        self.root.rowconfigure(3, weight=0)

#%% Shortcuts

    def _get_image_object(self, image_index):
        if image_index < len(self.cluster.images):
            return self.cluster.images[image_index]

    def _get_image_name (self, image_index):
        if image_index < len(self.cluster.images):
            return self.cluster.images[image_index].name

    def _add_to_identicals (self, left_image_name, right_image_name):
        found = False
        for s in self.cluster.identicals:
            if left_image_name in s:
                s.add(right_image_name)
                found = True

        if not found:
            self.cluster.identicals.append(set([left_image_name, right_image_name]))

    def _remove_from_identicals (self, left_image_name, right_image_name):
        for s in self.cluster.identicals:
            if left_image_name in s:
                s.remove(right_image_name)

    def _is_identical(self, left_image_name, right_image_name):
        for s in self.cluster.identicals:
            if left_image_name in s and right_image_name in s:
                return True
        return False

    def _update_cluster_label(self):
        right_cluster_label = self._get_image_object(self.right_image_index).cluster
        if len(right_cluster_label) > 40:
            right_cluster_label = right_cluster_label[:40] + "..."
        self.right_cluster_label.config(text = "Cluster : " + right_cluster_label)

        left_cluster_label = self._get_image_object(self.left_image_index).cluster
        if len(left_cluster_label) > 40:
            left_cluster_label = left_cluster_label[:40] + "..."
        self.left_cluster_label.config(text = "Cluster : " + left_cluster_label)

    def _update_image_label(self):
        if self._get_image_object(self.right_image_index):
            right_image_label = self._get_image_object(self.right_image_index).name
        else:
            right_image_label = ""
        if len(right_image_label ) > 40:
            right_image_label  = right_image_label [:40] + "..."
        self.right_image_name_label .config(text = "Name : " + right_image_label )

        left_image_label = self._get_image_object(self.left_image_index).name
        if len(left_image_label) > 40:
            left_image_label = left_image_label[:40] + "..."
        self.left_image_name_label.config(text = "Name : " + left_image_label)

    def _open_cluster(self, project_address):
        """Open an unfinished cluster.
        Create a Cluster object

        Return: Cluster object
        """
        #TODO read log then open undone cluster
        all_clusters = [f for f in os.listdir(project_address) if not f.startswith('.')]
        cluster_name =  all_clusters[0]
        cluster_address = os.path.join(project_address, cluster_name )

        #create cluster object
        return Cluster(folder_address = cluster_address)

    def _swap_positions(self, list, pos1, pos2):

        # popping both the elements from list
        first_ele = list.pop(pos1) 
        second_ele = list.pop(pos2-1)

        # inserting in each others positions
        list.insert(pos1, second_ele)
        list.insert(pos2, first_ele)

        return list
#%% Visuals and Aesthetics
    def add_image(self,  path, column, row, columspan, rowspan, parent, sticky="nsew"):

        image = Image.open(path)
        iw, ih = int(image.width), int(image.height)
        h = int(self.root.winfo_height() * 3/4)
        image = image.resize((math.ceil(h/ih * iw), h), Image. ANTIALIAS)
        img = ImageTk.PhotoImage(image)
        img_label = tk.Label(parent, image=img)
        img_label.image = img
        img_label.grid(column=column,
                       row=row,
                       columnspan=columspan,
                       rowspan=rowspan,
                       sticky=sticky)
        return img_label


    def initialize_image_display(self):
        """initialize left and right image display"""

        best_image_index = self.cluster.get_best_image_index()
        if best_image_index == 0:
            self.left_image_index = 0
            self.right_image_index = 1
        else:
            self.left_image_index = best_image_index
            self.right_image_index = 0

        self.project_title_label.config(text = str("Project Title: " + self.project_name))
        self.stage_label.config(text = str("Current Stage: " + self.stage.name))

        self.left_image.grid_forget()
        self.right_image.grid_forget()

        self.left_image, self.right_image = self.add_images(self.left_image_index, self.right_image_index)

        #update image info display
        self._update_image_label()
        self._update_cluster_label()


        self.update_icon_button_color()


    def add_icon(self, path, height, width,  column, row, columspan, rowspan, parent, sticky="nsew"):

        image = Image.open(path)
        image = image.resize((width, height), Image. ANTIALIAS)
        img = ImageTk.PhotoImage(image)
        img_label = tk.Label(parent, image=img)
        img_label.image = img
        img_label.grid(column=column,
                       row=row,
                       columnspan=columspan,
                       rowspan=rowspan,
                       sticky=sticky)
        return img_label

    def add_text(self, content, column, row, columspan, rowspan, parent, sticky="nsew"):
        text = tk.Label(parent, text=content)
        text.grid(column=column,
                  row=row,
                  columnspan=columspan,
                  rowspan=rowspan,
                  sticky=sticky)
        return text

    def add_button(self, content, func, height, width, column, row, columspan, rowspan, parent, sticky="nsew"):
        button_text = tk.StringVar()
        button = tk.Button(parent,
                           textvariable=button_text,
                           height=height,
                           width=width,
                           command=func,
                           font = ("Arial", "14"))
        button_text.set(content)
        button.grid(column=column,
                    row=row,
                    columnspan=columspan,
                    rowspan=rowspan,
                    sticky=sticky)

        return button

    def add_frame(self, column, row, columspan, rowspan, parent, sticky="nsew"):
        frame = tk.Frame(parent, padx=6, pady=6, bd=0, width = 640, height = 80)
        frame.grid(column=column,
                   row=row,
                   columnspan=columspan,
                   rowspan=rowspan,
                   sticky=sticky)

        return frame

    def add_filler(self, height, width, column, row, columspan, rowspan, parent, sticky="nsew", content = ""):
        filler = tk.Label(parent, width=width, height=height, text = content)
        filler.grid(column=column,
                    row=row,
                    columnspan=columspan,
                    rowspan=rowspan,
                    sticky=sticky)

        return filler


    def add_images (self, left_image_number, right_image_number):
        """Add left and right images at once

        Args:
            left_image_number ([int]): index of image in self.cluster.images
            right_image_number ([int]): index of image in self.cluster.images

        Returns:
            TK Widget: left and right image widgets
        """
        left_path = self._get_image_object(left_image_number).address
        left_image = self.add_image(left_path, 0, 1, 1, 1, self.root, sticky = "we")
        # self.add_filler(1, 1, 1, 0, 1, 4, self.root, sticky = "w") #divider
        right_path = self._get_image_object(right_image_number).address
        right_image = self.add_image(right_path, 2, 1, 1, 1, self.root, sticky = "we")

        #initialize tick and button style
        if self._has_been_checked(self._get_image_name(right_image_number)):
            self.change_tick_color("right", True)
        else:
            self.change_tick_color("right", False)

        if self._get_image_name(right_image_number) in self.cluster.matches:
            #the pair has been previously matched
            self.activate_button(self.match_btn)

        return left_image, right_image

    def change_tick_color (self, side, checked):
        """turn the "check" icon green or grey

        Args:
            tick_widget ([type]): [description]
            checked ([bool]): whether the image has been checked
        """
        if side == "left":
            tick_widget = self.left_tick
            frame_widget = self.left_info_bar

        else:
            tick_widget = self.right_tick
            frame_widget = self.right_info_bar

        tick_widget.grid_forget()
        if checked:
            tick_widget = self.add_icon("images/green_tick.png", 15, 15, 1, 0, 1, 1, frame_widget, sticky = "e")

        else:
            tick_widget = self.add_icon("images/grey_tick.png", 15, 15, 1, 0, 1, 1, frame_widget, sticky = "e")


    def update_icon_button_color (self):
        """When browsing through images, update icon and button styles based on what action has been done to the right image
        """
        #disable best image and identical button if stage is not 0
        if self.stage.stage_number != 0:
            self.identical_btn["state"] = "disabled"
            self.best_image_btn["state"] = "disabled"
        else:
            self.identical_btn["state"] = "normal"
            self.best_image_btn["state"] = "normal"

        #the pair has been previously matched
        if self._get_image_name(self.right_image_index) in self.cluster.matches:
            self.activate_button(self.match_btn)
            self.change_tick_color("right", True)

        else:
            self.deactivate_button(self.match_btn)
            self.change_tick_color("right", False)

        #if the pair has been unmatched:
        if self._get_image_name(self.right_image_index) in self.cluster.nomatches:
            self.activate_button(self.no_match_btn)
            self.change_tick_color("right", True)
        else:
            self.deactivate_button(self.no_match_btn)

        #if the pair are identicals:
        if self._is_identical(self._get_image_name(self.left_image_index), self._get_image_name(self.right_image_index)):
            self.activate_button(self.identical_btn)
        else:
            self.deactivate_button(self.identical_btn)


    def change_button_color (self, button_widget, new_fg = "black", new_font = ("Arial", "14")):
        button_widget.config (fg = new_fg, font = new_font)

    def activate_button (self, button_widget):
        self.change_button_color (button_widget, new_fg = "#dda15e", new_font = ("Arial", "14", "bold"))

    def deactivate_button (self, button_widget):
        self.change_button_color (button_widget, new_fg = "black", new_font = ("Arial", "14"))

#%% Actions
    def choose_project(self):

        #TODO: change starting index according to progress?

        self.progress_data = progress.checkout_progress()
        existing_projects = {d.split('/')[-1] for d in list(self.progress_data.keys())}
        if not existing_projects:
            return
        self.create_choose_project_window(existing_projects)
        self.project_address = os.getcwd() + "/projects/" + self.project_name

        self.progress_data, self.stage, self.cluster = progress.load_progress(self.project_address)
        self.singles = Cluster( str(self.project_address+ "/" + "Singles"))

        self.initialize_image_display()

        logger.info("Open existing project {}".format(self.project_name))

    def browse_files(self):
        """Let user choose which new project/folder to start working on
        pass the directory name to the class
        show images
        """

        #TODO: allow user to give project a name
        dirname = filedialog.askdirectory(parent=self.root)

        #check if the folder is valid
        valid = True
        for folder in os.listdir(dirname):
            if not folder.startswith("."):
                is_folder = os.path.isdir(dirname + "/" + folder)
                valid = valid and is_folder

        valid = valid and "Singles" in os.listdir(dirname)

        if not valid:
            tk.messagebox.askokcancel("Invalid folder", "The folder you have chosen is not valid." )
            return None

        self.project_name = dirname.split("/")[-1]
        self.project_address, self.progress_data = progress.start_new_project(dirname, self.project_name)
        self.stage = Stage(0, self.project_address)

        #open the first cluster
        self.cluster = self._open_cluster(project_address = self.project_address)

        #read or make Singles folder
        if not os.path.exists(dirname + "/" + "Singles"):
            os.mkdir(dirname + "/" + "Singles")
        self.singles = Cluster( str(dirname + "/" + "Singles"))

        #initialize image display
        self.initialize_image_display()

        #close pop-up
        self.open_window.destroy()

        logger.info("_____Create new project{}_____".format(self.project_name))
        return None

    def load_next_image (self):
        """Change right image. Erase old image, Add the next in line image. function for "next" button

        """
        #skip the index of left image
        self.right_image_index = min(len(self.cluster.images), self.right_image_index + 1)
        if self.right_image_index == self.left_image_index:
            self.right_image_index = min(len(self.cluster.images), self.right_image_index + 1)

        self.right_image.grid_forget()

        if self.right_image_index < len(self.cluster.images):
            new_image_path = self._get_image_object(self.right_image_index).address
            self.right_image = self.add_image(new_image_path, 2, 1, 1, 1, self.root, sticky = "we")
            self._update_cluster_label()
            self.update_icon_button_color ()

        else:
            self.add_filler(30,30, 2, 1, 1, 1, self.root, content = "End of Cluster")
            new_cluster_label = ""
            self.change_tick_color("right", False)
            self.deactivate_button(self.match_btn)
            self.deactivate_button(self.no_match_btn)
            self.deactivate_button(self.identical_btn)
            self.right_cluster_label.config(text = "Cluster: " + new_cluster_label)

        #update image labels
        self._update_image_label()

        #check for completion at the last image
        if self.right_image_index == len(self.cluster.images):
            self.check_completion_and_move_on()
        return None

    def load_prev_image (self):
        """ change right image
        When user reach the index 1 image, can't move forward anymore

        """
        #skip the index of left image
        self.right_image_index = max(0, self.right_image_index - 1)
        if self.right_image_index == self.left_image_index:
            if self.left_image_index == 0:
                self.right_image_index = 1
            else:
                self.right_image_index = max(0, self.right_image_index - 1)

        self.right_image.grid_forget()
        if self.right_image_index >= 0:
            new_image_path = self._get_image_object(self.right_image_index).address
            self.right_image = self.add_image(new_image_path, 2, 1, 1, 1, self.root, sticky = "we")
            self._update_image_label()
            self._update_cluster_label()
            self.update_icon_button_color ()

        return None

    def _has_been_checked(self, image_name):
        return image_name in self.cluster.matches or image_name in self.cluster.nomatches

    def cluster_validation_match (self):
        """During cluster validation stage, match left and right image
        - the right tick turn green (means checked)
        - the match button's fg turn orange
        - the right image object added to cluster.matchs
        - take object out from cluster.nomatches if init

        """
        if self.right_image_index < len(self.cluster.images):
            self.change_tick_color ("right", checked = True)
            self.activate_button(self.match_btn)

            self.cluster.matches.add(self._get_image_name(self.right_image_index))
            #delist from nomatches
            if self._get_image_name(self.right_image_index) in self.cluster.nomatches:
                self.cluster.nomatches.remove(self._get_image_name(self.right_image_index))
                self.deactivate_button(self.no_match_btn)
            logger.info("Match {} to cluster {}".format(self._get_image_name(self.right_image_index),self.cluster.name))


    def cluster_validation_no_match (self):
        """During cluster validation stage, unmatch left and right image
        - the right tick turn green (means checked)
        - the unmatch button's fg turn orange
        - the right image object added to cluster.unmatchs
        - remove right from cluster.matches
        - update right_cluster_label to "Singles"
        - update the image's cluster to singles

        """


        if self.right_image_index < len(self.cluster.images):
            self.change_tick_color ("right", checked = True)
            self.activate_button(self.no_match_btn)
            self.cluster.nomatches.add(self._get_image_name(self.right_image_index))
            #delist from matches
            if self._get_image_name(self.right_image_index) in self.cluster.matches:
                self.cluster.matches.remove(self._get_image_name(self.right_image_index))
                self.deactivate_button(self.match_btn)
            #delist from identicals
            if self._is_identical(self._get_image_name(self.left_image_index), self._get_image_name(self.right_image_index)):
                self._remove_from_identicals (self._get_image_name(self.left_image_index), self._get_image_name(self.right_image_index))
                self.deactivate_button(self.identical_btn)

            logger.info("Unmatch {} from cluster {}".format(self._get_image_name(self.right_image_index), self.cluster.name))


    def cluster_validation_identical (self):
        """During cluster validation stage, mark left and right images identical
        - the right tick turn green (means checked)
        - add right image to the hashmap cluster.identical
        - add current image to cluster.matches + activate match button
        - if previously in cluster.nomatches, remove it & deactivate nomatch button

        - if the two images are already marked identical, click this button will delist them from identicals
        """
        if self.right_image_index < len(self.cluster.images):

            self.change_tick_color ("right", checked = True)
            left, right = self._get_image_name(self.left_image_index), self._get_image_name(self.right_image_index)

            if self._is_identical(left,right):
                #delist form identicals
                self._remove_from_identicals(left,right)
                self.deactivate_button(self.identical_btn)

            else:
                #add to identicals
                self._add_to_identicals (left,right)
                self.activate_button(self.identical_btn)
                #add to matches
                self.cluster_validation_match()

            logger.info("Mark {} identical to {}".format(self._get_image_name(self.right_image_index), self._get_image_name(self.right_image_index)))


    def cluster_validation_best_image (self):
        """During cluster validation, mark right image the best image of the cluster
        - If the two images were marked unmatched, no effect
        - Make the right image cluster.best_image
        - Swap the left and right images
        """
        # if right image is already classified as single, no effect
        if self._get_image_name(self.right_image_index) in self.cluster.nomatches:
            return None

        #swap attributes
        best_image = self.right_image
        best_image_index = self.right_image_index

        self.cluster.best_image = self._get_image_object(best_image_index)

        self.right_image = self.left_image
        self.right_image_index = self.left_image_index

        self.left_image =best_image
        self.left_image_index = best_image_index

        #update image info display
        self._update_image_label()
        self._update_cluster_label()

        #swap pictures
        self.right_image.grid_forget()
        self.left_image.grid_forget()
        self.add_images(self.left_image_index, self.right_image_index)

        #if new right image has been matched to anything in the cluster before -> mark checked & match
        if len(self.cluster.matches) > 0:
            self.change_tick_color("right", True)
            self.activate_button(self.match_btn)
            self.cluster.matches.add(self._get_image_name(self.right_image_index))
            if self._get_image_name(self.left_image_index) in self.cluster.matches:
                self.cluster.matches.remove(self._get_image_name(self.left_image_index))

        else:
            self.change_tick_color("right", False)
            self.deactivate_button(self.match_btn)

        #swap the positions of the old best image (now right image) with the old right image (now left image) in the list
        self.cluster.images = self._swap_positions(self.cluster.images, self.right_image_index, self.left_image_index)
        #update left and right images' indices
        curr_left_index = self.left_image_index
        curr_right_index = self.right_image_index
        self.left_image_index = curr_right_index
        self.right_image_index = curr_left_index
        logger.info("Make {} best image for cluster {}".format(self._get_image_name(self.right_image_index), self.cluster.name))


    def check_completion_and_move_on (self):
        """This function is called when user clicks "next" while at the last image"""
        #don't mark complete till the user says "OK"

        if progress.check_cluster_completion(self.cluster):
            self.stage = progress.mark_cluster_completed(self.cluster,self.stage)

        if progress.check_project_completion(self.cluster, self.stage, self.project_address):
            logger.info("!!!!project complete!!!!")
            logger.info(str(self.progress_data))
            #ask user if wants to export and save
            response = self.create_export_results_window()
            if response:
                save_address = filedialog.askdirectory() # asks user to choose a directory
                if not save_address:
                    return None
                self.progress_data, self.cluster = progress.update_folder_and_record(self.progress_data, self.project_address, self.cluster, self.stage)
                progress.check_completion_and_save(self.cluster, self.stage, self.project_address, self.progress_data)
                self.progress_data, _, _ = progress.load_progress(self.project_address, False)
                progress.export_results(self.project_address,self.progress_data, save_address)
                logger.info("====EXPORT====")
                self.root.destroy()
            else:
                return None
        else:
            if progress.check_stage_completion(self.cluster, self.stage):
                message = "You have completed the current stage."
                logger.info("_____STAGE {} COMPLETED_____".format(self.stage.name))
            else:
                if progress.check_cluster_completion(self.cluster):
                    message = "You have completed the current cluster."
                else:
                    return None

            response = self.create_save_progress_window(message)
            if response:
                self.progress_data, self.cluster = progress.update_folder_and_record(self.progress_data, self.project_address, self.cluster, self.stage)
                progress.check_completion_and_save(self.cluster, self.stage, self.project_address, self.progress_data)
                self.progress_data, self.stage, self.cluster = progress.load_progress(self.project_address)

                if self.cluster:
                    #if next cluster has only 1 image, skip it & recurse
                    if len(self.cluster.images) <= 1:
                        logger.info("----SKIP ",self.cluster.name, "----")
                        self.stage = progress.mark_cluster_completed(self.cluster,self.stage)
                        self.progress_data, self.cluster = progress.update_folder_and_record(self.progress_data, self.project_address, self.cluster, self.stage)
                        progress.check_completion_and_save(self.cluster, self.stage, self.project_address, self.progress_data)
                        self.progress_data, self.stage, self.cluster = progress.load_progress(self.project_address)
                        self.check_completion_and_move_on ()
                    else:
                        self.initialize_image_display()
                if "stage" in message:
                    logger.info(str(self.progress_data))

    def save(self):
        """save results
        """
        if len(self.progress_data) > 0:
            self.progress_data, self.cluster = progress.update_folder_and_record(self.progress_data, self.project_address, self.cluster,self.stage)
            progress.check_completion_and_save(self.cluster, self.stage, self.project_address, self.progress_data)

    def exit(self):
        if len(self.progress_data) > 0:
            self.save()
        else:
            shutil.rmtree(self.project_address)
        logger.info(str(self.progress_data))
        logger.info("====EXIT====\n\n")
        self.root.destroy()

    def create_export_results_window(self):
        response = tk.messagebox.askokcancel("Export results", "You have completed the current project.\nExport the results?" )
        return response

    def create_save_progress_window(self, message):
        response = tk.messagebox.askokcancel("Save progress", message + "\nMove on to the next?" )
        return response

    def create_open_window(self):
        self.open_window = Toplevel(self.root)
        self.open_window.title("Open")
        self.open_window.geometry("300x200")
        self.new_project_button = tk.Button(self.open_window, text="   Start a new project   ", command = self.browse_files)
        self.new_project_button.place(relx=0.5, rely=0.3, anchor=CENTER)
        self.continue_existing_project = tk.Button(self.open_window, text="Continue existing project", command = self.choose_project)
        self.continue_existing_project.place(relx=0.5, rely=0.6, anchor=CENTER)
        self.open_window.mainloop()

    def create_choose_project_window(self, choices):
        self.choose_project_window = Toplevel(self.root)
        self.choose_project_window.title("Choose a project")
        self.choose_project_window.geometry("200x300")

        name = tk.StringVar()
        default_project_name = list(choices)[0]
        name.set(default_project_name)

        popupMenu = tk.OptionMenu(self.choose_project_window, name, *choices)
        popupMenu.place(relx=0.5, rely=0.3, anchor=CENTER)

        def exit():
            self.choose_project_window.quit()
            self.choose_project_window.destroy()
            self.open_window.quit()
            self.open_window.destroy()

        self.project_name = name.get()
        ok_button = tk.Button(self.choose_project_window, text = "OK", command = exit)
        ok_button.place(relx=0.5, rely=0.8, anchor=CENTER)
        self.choose_project_window.mainloop()

    def create_main_UI (self):

        #initialize left and right images
        self.left_image = self.add_filler(30,30, 0, 1, 1, 1, self.root, sticky = "w")
        _ = self.add_filler(1, 1, 1, 0, 1, 4, self.root, sticky = "w") #divider
        self.right_image = self.add_filler(30,30, 2, 1, 1, 1, self.root, sticky = "w")

        # menu bar
        right_menu_bar = self.add_frame(2, 0, 1, 1, self.root)
        right_menu_bar.rowconfigure(0, weight=1)
        right_menu_bar.columnconfigure(1, weight=1)
        _ = self.add_filler(1,1, 0, 0, 1, 1, right_menu_bar, sticky= "w")
        self.undo_btn = self.add_button("Undo", None, 2, 3, 1, 0, 1, 1, right_menu_bar, sticky = "e")
        self.open_btn = self.add_button("Open", self.create_open_window, 2, 3, 2, 0, 1, 1, right_menu_bar, sticky = "e")
        self.save_btn = self.add_button("Save", self.save, 2, 3, 3, 0, 1, 1, right_menu_bar, sticky = "e")
        self.exit_btn = self.add_button("Exit", self.exit, 2, 3, 4, 0, 1, 1, right_menu_bar, sticky = "e")

        left_menu_bar = self.add_frame(0, 0, 1, 1, self.root)
        left_menu_bar.columnconfigure(1, weight=1)
        self.project_title_label = self.add_text("Project Title: ", 0, 0, 1, 1, left_menu_bar, sticky= "w")
        self.stage_label = self.add_text("Current Stage: ", 0, 1, 1, 1, left_menu_bar, sticky= "w")

        # image info
        self.left_info_bar = self.add_frame(0, 2, 1, 1, self.root)
        self.left_info_bar.grid_propagate(0)
        self.left_info_bar.columnconfigure(1, weight=1)
        self.left_image_name_label = self.add_text("Name : ", 0, 0, 1, 1, self.left_info_bar, sticky= "w")
        self.left_cluster_label = self.add_text("Cluster : ", 0, 1, 1, 1, self.left_info_bar, sticky= "w")
        _ = self.add_filler(4, 4, 2, 0, 1, 2, self.left_info_bar, "e")

        self.right_info_bar = self.add_frame(2, 2, 1, 1, self.root)
        self.right_info_bar.grid_propagate(0)
        self.right_info_bar.columnconfigure(2, weight=1)

        self.right_image_name_label = self.add_text("Name : ", 0, 0, 1, 1, self.right_info_bar, sticky="w")
        self.right_cluster_label = self.add_text("Cluster : ", 0, 1, 1, 1, self.right_info_bar, sticky="w")

        self.right_tick = self.add_filler(1, 1, 1, 0, 1, 1, self.right_info_bar, sticky = "e")

        #navigation buttons
        self.prev_btn = self.add_button("Prev", self.load_prev_image, 4, 4, 2, 0, 1, 2, self.right_info_bar, sticky="e")
        self.next_btn = self.add_button("Next", self.load_next_image, 4, 4, 3, 0, 1, 2, self.right_info_bar, sticky="e")

        # action buttons
        action_bar = self.add_frame(2, 3, 1, 1, self.root)
        action_bar.rowconfigure(0, weight=1)
        for i in range(4):
            action_bar.columnconfigure(i, weight=1)
        self.match_btn = self.add_button("Match", self.cluster_validation_match, 2, 4, 0, 0, 1, 1, action_bar)
        self.no_match_btn = self.add_button("No Match", self.cluster_validation_no_match, 2, 4, 1, 0, 1, 1, action_bar)
        self.identical_btn = self.add_button("Identical", self.cluster_validation_identical, 2, 4, 2, 0, 1, 1, action_bar)
        self.best_image_btn = self.add_button("Best Image", self.cluster_validation_best_image, 2, 4, 3, 0, 1, 1, action_bar)


        #filler
        _ = self.add_frame(0, 3, 1, 1, self.root, "w")

    def start (self):
        self.create_main_UI()
        self.root.mainloop()

# %%
