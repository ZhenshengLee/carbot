#!/usr/bin/env python
# Lucas Walter
# June 2016
#
# Subscribe to a cmd_vel Twist message and interpret the linear
# and angular components into a joint state for the virtual steer joint.

import math
import rospy

from geometry_msgs.msg import Twist
from sensor_msgs.msg import JointState
from tf import transformations

# TODO(lucasw) put this in a module and import it
# get the angle to to the wheel from the spin center
def get_angle(self, tf_buffer, link, spin_center, steer_angle, stamp):
    # lookup the position of each link in the back axle frame
    ts = tf_buffer.lookup_transform(spin_center.header.frame_id, link,
                                    stamp, rospy.Duration(4.0))

    dy = ts.transform.translation.y - spin_center.point.y
    dx = ts.transform.translation.x - spin_center.point.x
    angle = math.atan2(dx, abs(dy))
    if steer_angle < 0:
        angle = -angle

    # visualize the trajectory forward or back of the current wheel
    # given the spin center
    radius = math.sqrt(dx * dx + dy * dy)


class CmdVelToJoint():
    def __init__(self):
        self.rate = rospy.get_param("~rate", 20.0)
        self.period = 1.0 / self.rate

        self.tf_buffer = tf2_ros.Buffer()
        self.tf = tf2_ros.TransformListener(self.tf_buffer)

        self.steer_link = rospy.get_param("~steer_link", "lead_steer")
        self.steer_joint = rospy.get_param("~steer_joint", "lead_steer_joint")
        self.wheel_joint = rospy.get_param("~wheel_joint", "wheel_lead_axle")
        self.wheel_radius = rospy.get_param("~wheel_radius", 0.15)
        # the spin center is always on the fixed axle y axis of the fixed axle,
        # it is assume zero rotation on the steer_joint puts the steering
        # at zero rotation with respect to fixed axle x axis (or xz plane)
        self.fixed_axle_link = rospy.get_param("~fixed_axle_link", "back_axle")

        self.steer_pub = rospy.Publisher("joint_states", JointState, queue_size=1)
        # TODO(lucasw) is there a way to get TwistStamped out of standard
        # move_base publishers?
        self.joint_state = JointState()
        self.joint_state.name.append(self.steer_joint)
        self.joint_state.position.append(0.0)
        self.joint_state.velocity.append(0.0)
        self.joint_state.name.append(self.wheel_joint)
        self.joint_state.position.append(0.0)
        self.joint_state.velocity.append(0.0)
        self.cmd_vel = None
        rospy.Subscriber("cmd_vel", Twist, self.cmd_vel_callback, queue_size=2)
        self.timer = rospy.Timer(rospy.Duration(self.period), self.update)

    def cmd_vel_callback(self, msg):
        self.cmd_vel = msg

    def update(self, event):
        if self.cmd_vel is None:
            return

        steer_transform = self.tf_buffer.lookup_transform(self.fixed_axle_link,
                                                          self.steer_link,
                                                          rospy.Time(),
                                                          rospy.Duration(4.0))
        joint_state.header.stamp = steer_transform.header.stamp
        # if the cmd_vel is pure linear x, then the joint state is at zero
        # steer angle (no skid steering modelled).
        if msg.linear.y == 0.0:
            self.joint_state.position[0] = 0.0
            self.joint_state.velocity[0] = 0.0
            wheel_angular_velocity = msg.linear.x / self.wheel_radius
            # TODO(lucasw) assuming fixed period for now, could
            # measure actual dt with event parameter.
            self.joint_state.position[1] += wheel_angular_velocity * self.period
            self.joint_state.velocity[1] = wheel_angular_velocity
        else:
            # need to calculate the steer angle
            # from the ratio of linear.y to linear.x

            # angle, lead_radius = self.get_angle(self.steer_link, spin_center,
            #                                             steer_angle, msg.header.stamp)
            # angle, radius = self.get_angle("base_link", spin_center,
            #                                steer_angle, msg.header.stamp)
            # fr = radius / lead_radius
            # distance = self.wheel_radius * lead_wheel_angular_velocity * fr * dt
            # angle_traveled = distance / radius
            # dx_in_ts = radius * math.sin(angle_traveled)
            # dy_in_ts = radius * (1.0 - math.cos(angle_traveled))
            # dy_in_ts/dx_in_ts = msg.linear.y / msg.linear.x
            # and then work backwards from above to get to lead_wheel_angular_velocity
            # TODO(lucasw) is lead_wheel_angular_velocity linear.x**2 + linear.y**2?

        self.steer_pub.publish(joint_state)

if __name__ == '__main__':
    rospy.init_node("cmd_vel_to_joint")
    cmd_vel_to_joint = CmdVelToJoint()
    rospy.spin()
