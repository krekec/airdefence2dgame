import pygame
import random
import math

class ExplosionEffect:
    def __init__(self, x, y, max_radius=100):
        self.x = x
        self.y = y
        self.max_explosion_radius = max_radius
        self.explosion_radius = 0
        self.explosion_speed = 5
        self.explosion_alpha = 255
        self.particles = []
        self.glow_particles = []
        self.smoke_particles = []
        self.screen_shake = 0
        self.explosion_phases = {
            'burst': {'duration': 10, 'current': 0},
            'expansion': {'duration': 30, 'current': 0},
            'dissipation': {'duration': 60, 'current': 0}
        }
        self.current_phase = 'burst'
        
        try:
            self.explosion_sound = pygame.mixer.Sound("explosion.mp3")
            self.explosion_sound.set_volume(0.3)
        except:
            print("Could not load explosion sound")
        
        self.create_particles()
        if hasattr(self, 'explosion_sound'):
            self.explosion_sound.play()

    def create_particles(self):
        # Core explosion particles
        num_particles = 40
        for _ in range(num_particles):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(3, 8)
            size = random.randint(4, 12)
            lifetime = random.randint(30, 60)
            self.particles.append({
                'x': 0, 'y': 0,
                'dx': math.cos(angle) * speed,
                'dy': math.sin(angle) * speed,
                'size': size,
                'original_size': size,
                'lifetime': lifetime,
                'max_lifetime': lifetime,
                'color': random.choice([(255, 255, 200), (255, 200, 0), (255, 165, 0)]),
                'phase': 'burst',
                'acceleration': random.uniform(0.92, 0.98)
            })
        
        # Glow particles
        for _ in range(15):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 3)
            size = random.randint(20, 40)
            lifetime = random.randint(40, 70)
            self.glow_particles.append({
                'x': 0, 'y': 0,
                'dx': math.cos(angle) * speed,
                'dy': math.sin(angle) * speed,
                'size': size,
                'lifetime': lifetime,
                'max_lifetime': lifetime,
                'color': (255, 200, 100),
                'alpha': random.randint(100, 180)
            })

        # Smoke particles
        for _ in range(30):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 4)
            size = random.randint(8, 15)
            lifetime = random.randint(50, 80)
            self.smoke_particles.append({
                'x': 0, 'y': 0,
                'dx': math.cos(angle) * speed * 0.5,
                'dy': math.sin(angle) * speed * 0.5 - 0.3,
                'size': size,
                'growth_rate': random.uniform(0.2, 0.4),
                'lifetime': lifetime,
                'max_lifetime': lifetime,
                'alpha': random.randint(180, 255),
                'rotation': random.uniform(0, 360),
                'rotation_speed': random.uniform(-2, 2)
            })

    def update_explosion_phase(self):
        if self.current_phase == 'burst':
            self.explosion_phases['burst']['current'] += 1
            if self.explosion_phases['burst']['current'] >= self.explosion_phases['burst']['duration']:
                self.current_phase = 'expansion'
        elif self.current_phase == 'expansion':
            self.explosion_phases['expansion']['current'] += 1
            if self.explosion_phases['expansion']['current'] >= self.explosion_phases['expansion']['duration']:
                self.current_phase = 'dissipation'
        else:  # dissipation phase
            self.explosion_phases['dissipation']['current'] += 1

    def update(self):
        self.update_explosion_phase()
        
        # Screen shake effect
        if self.current_phase == 'burst':
            self.screen_shake = random.randint(-5, 5)
        else:
            self.screen_shake = max(0, self.screen_shake * 0.9)

        # Update core particles
        for particle in self.particles:
            if particle['lifetime'] > 0:
                if self.current_phase == 'burst':
                    particle['dx'] *= 1.1
                    particle['dy'] *= 1.1
                elif self.current_phase == 'expansion':
                    particle['dx'] *= particle['acceleration']
                    particle['dy'] *= particle['acceleration']
                else:  # dissipation
                    particle['dx'] *= 0.98
                    particle['dy'] *= 0.98
                    particle['size'] *= 0.98

                particle['x'] += particle['dx']
                particle['y'] += particle['dy']
                particle['lifetime'] -= 1

        # Update glow particles
        for particle in self.glow_particles:
            if particle['lifetime'] > 0:
                particle['x'] += particle['dx'] * 0.5
                particle['y'] += particle['dy'] * 0.5
                particle['size'] *= 0.98
                particle['lifetime'] -= 1
                particle['alpha'] = int((particle['lifetime'] / particle['max_lifetime']) * 180)

        # Update smoke particles
        for particle in self.smoke_particles:
            if particle['lifetime'] > 0:
                particle['x'] += particle['dx']
                particle['y'] += particle['dy']
                particle['lifetime'] -= 1
                particle['size'] += particle['growth_rate']
                particle['alpha'] = int((particle['lifetime'] / particle['max_lifetime']) * 155)
                particle['rotation'] += particle['rotation_speed']
                particle['dx'] += random.uniform(-0.1, 0.1)
                particle['dy'] += random.uniform(-0.1, 0.1)

    def draw(self, screen):
        if self.explosion_alpha > 0:
            explosion_size = int(self.max_explosion_radius * 3)
            explosion_surface = pygame.Surface((explosion_size, explosion_size), pygame.SRCALPHA)
            center = (explosion_size // 2, explosion_size // 2)

            
            for particle in self.glow_particles:
                if particle['lifetime'] > 0:
                    pos = (int(center[0] + particle['x']), int(center[1] + particle['y']))
                    radius = int(particle['size'])
                    for r in range(radius, 0, -2):
                        alpha = int((r / radius) * particle['alpha'])
                        pygame.draw.circle(explosion_surface, (*particle['color'], alpha), pos, r)

            
            for particle in self.particles:
                if particle['lifetime'] > 0:
                    life_ratio = particle['lifetime'] / particle['max_lifetime']
                    pos = (int(center[0] + particle['x']), int(center[1] + particle['y']))
                    
                    if life_ratio > 0.7:
                        color = (255, 255, 255)
                    elif life_ratio > 0.4:
                        color = particle['color']
                    else:
                        color = tuple(max(c - 100, 0) for c in particle['color'])
                    
                    alpha = int(255 * life_ratio)
                    size = int(particle['size'] * (0.5 + life_ratio * 0.5))
                    pygame.draw.circle(explosion_surface, (*color, alpha), pos, size)

           
            for particle in self.smoke_particles:
                if particle['lifetime'] > 0:
                    pos = (int(center[0] + particle['x']), int(center[1] + particle['y']))
                    smoke_surface = pygame.Surface((int(particle['size'] * 2), int(particle['size'] * 2)), pygame.SRCALPHA)
                    
                    for r in range(int(particle['size']), 0, -1):
                        alpha = int((r / particle['size']) * particle['alpha'] * 0.7)
                        pygame.draw.circle(smoke_surface, (80, 80, 80, alpha), 
                                        (int(particle['size']), int(particle['size'])), r)
                    
                    rotated_smoke = pygame.transform.rotate(smoke_surface, particle['rotation'])
                    smoke_rect = rotated_smoke.get_rect(center=pos)
                    explosion_surface.blit(rotated_smoke, smoke_rect)

           
            shake_offset = (self.screen_shake, self.screen_shake) if self.current_phase == 'burst' else (0, 0)
            explosion_rect = explosion_surface.get_rect(center=(self.x + shake_offset[0], self.y + shake_offset[1]))
            screen.blit(explosion_surface, explosion_rect)

    def is_finished(self):
        return (all(p['lifetime'] <= 0 for p in self.particles) and
                all(p['lifetime'] <= 0 for p in self.glow_particles) and
                all(p['lifetime'] <= 0 for p in self.smoke_particles))