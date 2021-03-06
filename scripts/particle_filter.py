#!/usr/bin/env python3

import rospy

from nav_msgs.msg import OccupancyGrid
from geometry_msgs.msg import Quaternion, Point, Pose, PoseArray, PoseStamped
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Header, String

import tf
from tf import TransformListener
from tf import TransformBroadcaster
from tf.transformations import quaternion_from_euler, euler_from_quaternion

import random
import numpy as np
from numpy.random import random_sample
from numpy.random import randint
import math
from copy import deepcopy

from random import randint, random, sample

from sklearn.neighbors import NearestNeighbors
from likelihood_field import LikelihoodField

def get_yaw_from_pose(p):
    """ A helper function that takes in a Pose object (geometry_msgs) and returns yaw"""

    yaw = (euler_from_quaternion([
            p.orientation.x,
            p.orientation.y,
            p.orientation.z,
            p.orientation.w])
            [2])

    return yaw


def draw_random_sample(choices, probabilities, n):
    """ Return a random sample of n elements from the set choices with the specified probabilities
        choices: the values to sample from represented as a list
        probabilities: the probability of selecting each element in choices represented as a list
        n: the number of samples
    """
    values = np.array(range(len(choices)))
    probs = np.array(probabilities)
    bins = np.add.accumulate(probs)
    inds = values[np.digitize(random_sample(n), bins)]
    samples = []
    for i in inds:
        samples.append(deepcopy(choices[int(i)]))
    return samples


    # Taken from Lesson 06
def compute_prob_zero_centered_gaussian(dist, sd):
    """ Takes in distance from zero (dist) and standard deviation (sd) for gaussian
        and returns probability (likelihood) of observation """
    c = 1.0 / (sd * math.sqrt(2 * math.pi))
    prob = c * math.exp((-math.pow(dist,2))/(2 * math.pow(sd, 2)))
    return prob




class Particle:

    def __init__(self, pose, w):

        # particle pose (Pose object from geometry_msgs)
        self.pose = pose

        # particle weight
        self.w = w



class ParticleFilter:


    def __init__(self):

        # once everything is setup initialized will be set to true
        self.initialized = False        


        # initialize this particle filter node
        rospy.init_node('turtlebot3_particle_filter')

        # set the topic names and frame names
        self.base_frame = "base_footprint"
        self.map_topic = "map"
        self.odom_frame = "odom"
        self.scan_topic = "scan"

        # inialize our map and occupancy field
        self.map = OccupancyGrid()
        self.occupancy_field = None


        # the number of particles used in the particle filter
        self.num_particles = 2500

        # initialize the particle cloud array
        self.particle_cloud = []

        # initialize the estimated robot pose
        self.robot_estimate = Pose()

        # set threshold values for linear and angular movement before we preform an update
        self.lin_mvmt_threshold = 0.2        
        self.ang_mvmt_threshold = (np.pi / 6)

        self.odom_pose_last_motion_update = None

        


        # Setup publishers and subscribers

        # publish the current particle cloud
        self.particles_pub = rospy.Publisher("particle_cloud", PoseArray, queue_size=10)

        # publish the estimated robot pose
        self.robot_estimate_pub = rospy.Publisher("estimated_robot_pose", PoseStamped, queue_size=10)

        # subscribe to the map server
        rospy.Subscriber(self.map_topic, OccupancyGrid, self.get_map)

        # subscribe to the lidar scan from the robot
        rospy.Subscriber(self.scan_topic, LaserScan, self.robot_scan_received)

        # enable listening for and broadcasting corodinate transforms
        self.tf_listener = TransformListener()
        self.tf_broadcaster = TransformBroadcaster()


        # intialize the particle cloud
        self.initialize_particle_cloud()


        # For finding closest obstacles.        
        self.likelihood_field = LikelihoodField()


        self.publish_particle_cloud()
        print ("ready!")

        self.initialized = True



    def get_map(self, data):
        self.map = data
   


    def initialize_particle_cloud(self):
	# initialize particle positions
    #ocucpancy check
        initial_particle_set = []
        res = self.map.info.resolution
        origin_x = self.map.info.origin.position.x
        origin_y = self.map.info.origin.position.y
        shiftx = origin_x/res # map from occupancy grid to rviz
        shifty = origin_x/res
        i=0
        while (i < self.num_particles):
            x = randint(0,self.map.info.width)
            y = randint(0,self.map.info.height)
            ind = x + y*self.map.info.width
            if (ind >= len(self.map.data)):
                continue
            if self.map.data[ind] != -1 and self.map.data[ind] != 100:
                     i += 1
                     theta = 2 * np.pi*float(randint(1,1000))/1000
                     x = float(x+shiftx)*res
                     y = float(y+shifty)*res
                     initial_particle_set.append([x,y,theta])

        # assign positions to particles
        for i in range(len(initial_particle_set)):
            p = Pose()
            p.position = Point()
            p.position.x = initial_particle_set[i][0]
            p.position.y = initial_particle_set[i][1]
            p.position.z = 0
            p.orientation = Quaternion()
            q = quaternion_from_euler(0.0, 0.0, initial_particle_set[i][2])
            p.orientation.x = q[0]                                             
            p.orientation.y = q[1]
            p.orientation.z = q[2]
            p.orientation.w = q[3]
	    	#initialize the new particle, where all will have the same weight (1.0)
            new_particle = Particle(p, 1.0)      
	    	#append the particle to the particle cloud
            self.particle_cloud.append(new_particle)
        self.normalize_particles()
        #self.publish_particle_cloud()


    def normalize_particles(self):
        # make all the particle weights sum to 1.0
        w_sum = 0

        # get the sum
        for p in self.particle_cloud:
            w_sum += p.w

        # normalize the weights
        for p in self.particle_cloud:
             p.w /= w_sum




    def publish_particle_cloud(self):
        particle_cloud_pose_array = PoseArray()
        particle_cloud_pose_array.header = Header(stamp=rospy.Time.now(), frame_id=self.map_topic)
        particle_cloud_pose_array.poses
        for part in self.particle_cloud:
            particle_cloud_pose_array.poses.append(part.pose)
            self.particles_pub.publish(particle_cloud_pose_array)




    def publish_estimated_robot_pose(self):

        robot_pose_estimate_stamped = PoseStamped()
        robot_pose_estimate_stamped.pose = self.robot_estimate
        robot_pose_estimate_stamped.header = Header(stamp=rospy.Time.now(), frame_id=self.map_topic)
        self.robot_estimate_pub.publish(robot_pose_estimate_stamped)



    def resample_particles(self):
             # build an array of particle weights
        probabilities = []
        for p in self.particle_cloud:
            probabilities.append(p.w)

         # resample and update particle_cloud
        self.particle_cloud = draw_random_sample(self.particle_cloud, probabilities, self.num_particles)


    def robot_scan_received(self, data):

        # wait until initialization is complete
        if not(self.initialized):
            return

        # we need to be able to transfrom the laser frame to the base frame
        if not(self.tf_listener.canTransform(self.base_frame, data.header.frame_id, data.header.stamp)):
            return

        # wait for a little bit for the transform to become avaliable (in case the scan arrives
        # a little bit before the odom to base_footprint transform was updated) 
        self.tf_listener.waitForTransform(self.base_frame, self.odom_frame, data.header.stamp, rospy.Duration(0.5))
        if not(self.tf_listener.canTransform(self.base_frame, data.header.frame_id, data.header.stamp)):
            return

        # calculate the pose of the laser distance sensor 
        p = PoseStamped(
            header=Header(stamp=rospy.Time(0),
                          frame_id=data.header.frame_id))

        self.laser_pose = self.tf_listener.transformPose(self.base_frame, p)

        # determine where the robot thinks it is based on its odometry
        p = PoseStamped(
            header=Header(stamp=data.header.stamp,
                          frame_id=self.base_frame),
            pose=Pose())

        self.odom_pose = self.tf_listener.transformPose(self.odom_frame, p)

        # we need to be able to compare the current odom pose to the prior odom pose
        # if there isn't a prior odom pose, set the odom_pose variable to the current pose
        if not self.odom_pose_last_motion_update:
            self.odom_pose_last_motion_update = self.odom_pose
            return


        if self.particle_cloud:

            # check to see if we've moved far enough to perform an update

            curr_x = self.odom_pose.pose.position.x
            old_x = self.odom_pose_last_motion_update.pose.position.x
            curr_y = self.odom_pose.pose.position.y
            old_y = self.odom_pose_last_motion_update.pose.position.y
            curr_yaw = get_yaw_from_pose(self.odom_pose.pose)
            old_yaw = get_yaw_from_pose(self.odom_pose_last_motion_update.pose)



            if (np.abs(curr_x - old_x) > self.lin_mvmt_threshold or 
                np.abs(curr_y - old_y) > self.lin_mvmt_threshold or
                np.abs(curr_yaw - old_yaw) > self.ang_mvmt_threshold):

                # This is where the main logic of the particle filter is carried out

                self.update_particles_with_motion_model()

                self.update_particle_weights_with_measurement_model(data)

                self.normalize_particles()

                self.resample_particles()

                self.normalize_particles()

                self.update_estimated_robot_pose()

                self.publish_particle_cloud()
                self.publish_estimated_robot_pose()

                self.odom_pose_last_motion_update = self.odom_pose

                print ("Update done!")

    def update_estimated_robot_pose(self):
        # based on the particles within the particle cloud, update the robot pose estimate

        # Calculating weighted averages...
        eX = 0
        eY = 0
        eCos = 0
        eSin = 0

        for p in self.particle_cloud:
            eX += p.pose.position.x * p.w
            eY += p.pose.position.y * p.w
            yaw =  get_yaw_from_pose(p.pose)
            eCos += math.cos(yaw) * p.w
            eSin += math.sin(yaw) * p.w
        
            
        # Construct the average yaw.
        eTheta = math.atan2(eSin,eCos)
        
        # Updating the estimated pose.
        self.robot_estimate.position.x = eX
        self.robot_estimate.position.y = eY
        q = quaternion_from_euler(0, 0, eTheta)
        self.robot_estimate.orientation.x = q[0]
        self.robot_estimate.orientation.y = q[1]
        self.robot_estimate.orientation.z = q[2]
        self.robot_estimate.orientation.w = q[3]


        

    def update_particle_weights_with_measurement_model(self, data):
        
        # Feel free to add more if needed.
        range_values = range(0, 359, 10)

        for p in self.particle_cloud:
            q = 1
            # Do this for each range value
            for r in range_values:
                ztk = data.ranges[r]
                if (ztk > 3.5):
                    ztk = 3.5


                theta = get_yaw_from_pose(p.pose)

                xval = p.pose.position.x + ztk * math.cos(theta + (r * math.pi / 180.0))
                yval = p.pose.position.y + ztk * math.sin(theta + (r * math.pi / 180.0))

                dist = self.likelihood_field.get_closest_obstacle_distance(xval, yval)
                if (np.isnan(dist)):
                    q = 0
                    continue

                #print (dist)
                prob = compute_prob_zero_centered_gaussian(dist, 0.8) 
                q *= prob
            p.w = q

        

    def update_particles_with_motion_model(self):

        # based on the how the robot has moved (calculated from its odometry), we'll  move
        # all of the particles correspondingly

        # The current and previous odometer readings
        curr = self.odom_pose.pose
        old  = self.odom_pose_last_motion_update.pose


        # Find the change in x, y, theta/yaw
        curr_x = curr.position.x
        old_x  = old.position.x
        dx = curr_x - old_x

        curr_y = curr.position.y
        old_y = old.position.y     
        dy = curr_y - old_y 

        curr_yaw = get_yaw_from_pose(curr)
        old_yaw = get_yaw_from_pose(old)        
        dyaw = curr_yaw - old_yaw





        # Apply these changes to each particle.
        for p in self.particle_cloud:
            p.pose.position.x += dx
            p.pose.position.y += dy
            
            point_yaw = get_yaw_from_pose(p.pose)


             # NOISE APPLICATION: ADJUST BY RANDOM AMOUNT
             # Feel free to comment this section out if you do not want to consider noise.
            p.pose.position.x += float(randint(-15,15))/100
            p.pose.position.y += float(randint(-15,15))/200
            point_yaw += math.pi * float(randint(-200, 200))/2000




            q = quaternion_from_euler(0.0, 0.0, point_yaw + dyaw)

            p.pose.orientation.x = q[0]                                             
            p.pose.orientation.y = q[1]
            p.pose.orientation.z = q[2]
            p.pose.orientation.w = q[3]













if __name__=="__main__":
    

    pf = ParticleFilter()

    rospy.spin()
