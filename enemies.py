import pygame
import random
from heapq import heappush, heappop

class Enemy:
    def __init__(self, x, y, tile_size, game_map):
        self.size = tile_size // 2
        self.hitbox = pygame.Rect(
            x + (tile_size - self.size) // 2,
            y + (tile_size - self.size) // 2,
            self.size,
            self.size
        )
        self.color = (0, 255, 0)
        self.speed = 2
        self.tile_size = tile_size
        self.game_map = game_map
        self.path = []  # Store the path to the player
        self.path_update_cooldown = 0  # To avoid recalculating path every frame

    def update(self, player):
        # Update path to player every few frames to save performance
        if self.path_update_cooldown <= 0:
            player_tile = (player.hitbox.centerx // self.tile_size, player.hitbox.centery // self.tile_size)
            enemy_tile = (self.hitbox.centerx // self.tile_size, self.hitbox.centery // self.tile_size)
            self.path = self._a_star(enemy_tile, player_tile)
            self.path_update_cooldown = 10  # Recalculate path every 10 frames
        else:
            self.path_update_cooldown -= 1

        # Follow the path
        if self.path and len(self.path) > 1:
            next_tile = self.path[1]  # Skip the current tile (path[0])
            target_x = next_tile[0] * self.tile_size + (self.tile_size - self.size) // 2
            target_y = next_tile[1] * self.tile_size + (self.tile_size - self.size) // 2

            # Move toward the next tile in the path
            dx = target_x - self.hitbox.x
            dy = target_y - self.hitbox.y
            distance = (dx**2 + dy**2)**0.5

            if distance > 1:  # Avoid tiny movements when very close
                dx = (dx / distance) * self.speed if distance != 0 else 0
                dy = (dy / distance) * self.speed if distance != 0 else 0

                # Store old position
                old_x, old_y = self.hitbox.x, self.hitbox.y

                # Apply movement
                self.hitbox.x += dx
                self.hitbox.y += dy

                # Check for collisions with walls
                if self._check_collision():
                    self.hitbox.x = old_x
                    self.hitbox.y = old_y
                    self.path = []  # Clear path if stuck, forcing recalculation

        # Check player collision
        if self.hitbox.colliderect(player.hitbox):
            print("Le joueur est touché !")

    def _a_star(self, start, goal):
        """A* pathfinding algorithm to find the shortest path from start to goal."""
        if not (0 <= start[0] < len(self.game_map.tiles[0]) and 0 <= start[1] < len(self.game_map.tiles)):
            return []
        if not (0 <= goal[0] < len(self.game_map.tiles[0]) and 0 <= goal[1] < len(self.game_map.tiles)):
            return []

        # Priority queue for A* (min-heap)
        open_set = []
        heappush(open_set, (0, start))  # (f_score, position)
        
        # Track where we came from for path reconstruction
        came_from = {}
        
        # g_score: cost from start to current node
        g_score = {start: 0}
        
        # f_score: g_score + heuristic (estimated total cost)
        f_score = {start: self._heuristic(start, goal)}
        
        # Set of nodes already evaluated
        closed_set = set()
        
        while open_set:
            current = heappop(open_set)[1]
            
            if current == goal:
                # Reconstruct path
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                return path[::-1]  # Reverse path to go from start to goal
            
            closed_set.add(current)
            
            # Check neighboring tiles (up, down, left, right)
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                neighbor = (current[0] + dx, current[1] + dy)
                
                # Check if neighbor is within bounds and not a wall
                if (0 <= neighbor[0] < len(self.game_map.tiles[0]) and 
                    0 <= neighbor[1] < len(self.game_map.tiles) and 
                    not self.game_map.tile_kinds[self.game_map.tiles[neighbor[1]][neighbor[0]]].is_solid):
                    
                    if neighbor in closed_set:
                        continue
                    
                    tentative_g_score = g_score[current] + 1
                    
                    if neighbor not in [pos for _, pos in open_set]:
                        heappush(open_set, (f_score.get(neighbor, float('inf')), neighbor))
                    elif tentative_g_score >= g_score.get(neighbor, float('inf')):
                        continue
                    
                    # This is the best path so far
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = g_score[neighbor] + self._heuristic(neighbor, goal)
        
        return []  # No path found

    def _heuristic(self, a, b):
        """Manhattan distance heuristic for A*."""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _check_collision(self):
        """Optimized collision check using nearby tiles only"""
        start_x = max(0, self.hitbox.left // self.tile_size - 1)
        end_x = min(len(self.game_map.tiles[0]), (self.hitbox.right // self.tile_size) + 1)
        start_y = max(0, self.hitbox.top // self.tile_size - 1)
        end_y = min(len(self.game_map.tiles), (self.hitbox.bottom // self.tile_size) + 1)

        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                if self.game_map.tile_kinds[self.game_map.tiles[y][x]].is_solid:
                    wall_rect = pygame.Rect(
                        x * self.tile_size,
                        y * self.tile_size,
                        self.tile_size,
                        self.tile_size
                    )
                    if self.hitbox.colliderect(wall_rect):
                        return True
        return False

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.hitbox)