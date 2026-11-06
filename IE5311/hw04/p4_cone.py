import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from ppl import Variable, C_Polyhedron, Constraint_System

G1 = np.array([1.0, 0.0, 1.0])
G2 = np.array([0.0, 1.0, 1.0])
TMAX = 2.0


def lifted_cone_polyhedron():
    y1, y2, t = Variable(0), Variable(1), Variable(2)
    cs = Constraint_System()
    cs.insert(y1 >= 0)
    cs.insert(y2 >= 0)
    cs.insert(y1 + y2 - t == 0)
    return C_Polyhedron(cs)


def projection(poly):
    p = C_Polyhedron(poly)
    p.remove_higher_space_dimensions(2)
    return p


def report():
    cu = lifted_cone_polyhedron()
    print("C_U = {(y1,y2,t) : y1 >= 0, y2 >= 0, y1 + y2 - t = 0}")
    print("affine dimension:", cu.affine_dimension())
    print("generators:")
    for g in cu.minimized_generators():
        print("   ", g)

    y1, y2, t = Variable(0), Variable(1), Variable(2)
    cs = Constraint_System()
    cs.insert(y1 >= 0)
    cs.insert(y2 >= 0)
    cs.insert(y1 + y2 - t == 0)
    cs.insert(t <= -1)
    print("t >= 0 is implied:", C_Polyhedron(cs).is_empty())

    pr = projection(cu)
    print("projection onto (y1,y2):")
    for c in pr.minimized_constraints():
        print("   ", c)
    for g in pr.minimized_generators():
        print("   ", g)
    print("projection equals the nonnegative orthant = cone(U)")


def figure():
    fig = plt.figure(figsize=(11.0, 4.2))

    ax = fig.add_subplot(1, 3, 1)
    ax.plot([1, 0], [0, 1], color="black", linewidth=2.0)
    ax.plot([1, 0], [0, 1], "o", color="black", markersize=5)
    ax.set_xlim(-0.3, 1.6)
    ax.set_ylim(-0.3, 1.6)
    ax.set_aspect("equal")
    ax.set_xlabel("$x_1$")
    ax.set_ylabel("$x_2$")
    ax.set_title(r"$U=\{x\in\mathbb{R}^2_+:\;x_1+x_2=1\}$", fontsize=10)
    ax.axhline(0, color="0.6", linewidth=0.6)
    ax.axvline(0, color="0.6", linewidth=0.6)

    ax = fig.add_subplot(1, 3, 2, projection="3d")
    tri = np.array([[0, 0, 0], TMAX * G1, TMAX * G2])
    ax.add_collection3d(Poly3DCollection([tri], facecolor="0.75",
                                         edgecolor="black", alpha=0.55,
                                         linewidths=1.0))
    for g in (G1, G2):
        ax.plot(*zip([0, 0, 0], TMAX * g), color="black", linewidth=1.8)
    ax.plot(*zip(G1, G2), color="black", linewidth=2.2)
    ax.scatter(*zip(G1, G2), color="black", s=22)
    ax.set_xlim(0, TMAX)
    ax.set_ylim(0, TMAX)
    ax.set_zlim(0, TMAX)
    ax.set_xlabel("$y_1$")
    ax.set_ylabel("$y_2$")
    ax.set_zlabel("$t$")
    ax.set_title("$\\mathcal{C}_U$, with $U$ at $t=1$", fontsize=10)
    ax.view_init(elev=22, azim=38)

    ax = fig.add_subplot(1, 3, 3)
    ax.add_patch(Polygon([[0, 0], [1.6, 0], [1.6, 1.6], [0, 1.6]],
                         facecolor="0.75", edgecolor="black", alpha=0.55))
    ax.plot([1, 0], [0, 1], color="black", linewidth=2.0)
    ax.set_xlim(-0.3, 1.6)
    ax.set_ylim(-0.3, 1.6)
    ax.set_aspect("equal")
    ax.set_xlabel("$y_1$")
    ax.set_ylabel("$y_2$")
    ax.set_title("$\\mathrm{Proj}_{\\mathbb{R}^2}(\\mathcal{C}_U)"
                 "=\\mathrm{cone}(U)=\\mathbb{R}^2_+$", fontsize=10)
    ax.axhline(0, color="0.6", linewidth=0.6)
    ax.axvline(0, color="0.6", linewidth=0.6)

    fig.tight_layout()
    fig.savefig("p4_cone.pdf")
    fig.savefig("p4_cone.png", dpi=160)
    print("wrote p4_cone.pdf and p4_cone.png")


if __name__ == "__main__":
    report()
    figure()
