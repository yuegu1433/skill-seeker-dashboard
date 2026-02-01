/**
 * useSkills Hook Usage Examples
 *
 * Comprehensive examples showing how to use skills-related hooks.
 */

import React from 'react';
import { useSkills, useSkill, useSearchSkills, useCreateSkill, useUpdateSkill, useDeleteSkill } from './useSkills';

// Example 1: Basic skills listing with filters
export const BasicSkillsList: React.FC = () => {
  const { data, isLoading, error } = useSkills({
    platforms: ['claude', 'gemini'],
    statuses: ['completed'],
    page: 1,
    limit: 20,
  });

  if (isLoading) return <div>Loading skills...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      {data?.data.map((skill) => (
        <SkillCard key={skill.id} skill={skill} />
      ))}
    </div>
  );
};

// Example 2: Single skill detail view
export const SkillDetail: React.FC<{ skillId: string }> = ({ skillId }) => {
  const { data: skill, isLoading, error } = useSkill(skillId);

  if (isLoading) return <div>Loading skill...</div>;
  if (error) return <div>Error: {error.message}</div>;
  if (!skill) return <div>Skill not found</div>;

  return (
    <div>
      <h1>{skill.name}</h1>
      <p>{skill.description}</p>
      <p>Platform: {skill.platform}</p>
      <p>Status: {skill.status}</p>
    </div>
  );
};

// Example 3: Skills search with debouncing
export const SkillsSearch: React.FC = () => {
  const [query, setQuery] = React.useState('');
  const { data: searchResults, isLoading } = useSearchSkills(query, {
    platforms: ['claude'],
  });

  return (
    <div>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search skills..."
      />
      {isLoading && <div>Searching...</div>}
      <div>
        {searchResults?.map((skill) => (
          <SkillCard key={skill.id} skill={skill} />
        ))}
      </div>
    </div>
  );
};

// Example 4: Creating a new skill with form
export const CreateSkillForm: React.FC = () => {
  const createSkill = useCreateSkill();
  const [formData, setFormData] = React.useState({
    name: '',
    description: '',
    platform: 'claude',
    tags: [] as string[],
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createSkill.mutate(formData, {
      onSuccess: () => {
        setFormData({ name: '', description: '', platform: 'claude', tags: [] });
      },
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        value={formData.name}
        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
        placeholder="Skill name"
        required
      />
      <textarea
        value={formData.description}
        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
        placeholder="Description"
        required
      />
      <select
        value={formData.platform}
        onChange={(e) => setFormData({ ...formData, platform: e.target.value })}
      >
        <option value="claude">Claude</option>
        <option value="gemini">Gemini</option>
      </select>
      <button type="submit" disabled={createSkill.isPending}>
        {createSkill.isPending ? 'Creating...' : 'Create Skill'}
      </button>
      {createSkill.isError && <div>Error: {createSkill.error.message}</div>}
    </form>
  );
};

// Example 5: Editing a skill inline
export const EditableSkill: React.FC<{ skillId: string }> = ({ skillId }) => {
  const { data: skill, isLoading } = useSkill(skillId);
  const updateSkill = useUpdateSkill();
  const [isEditing, setIsEditing] = React.useState(false);
  const [editData, setEditData] = React.useState({ name: '', description: '' });

  React.useEffect(() => {
    if (skill) {
      setEditData({ name: skill.name, description: skill.description });
    }
  }, [skill]);

  const handleSave = () => {
    updateSkill.mutate(
      { id: skillId, data: editData },
      {
        onSuccess: () => setIsEditing(false),
      }
    );
  };

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      {isEditing ? (
        <>
          <input
            type="text"
            value={editData.name}
            onChange={(e) => setEditData({ ...editData, name: e.target.value })}
          />
          <textarea
            value={editData.description}
            onChange={(e) => setEditData({ ...editData, description: e.target.value })}
          />
          <button onClick={handleSave} disabled={updateSkill.isPending}>
            Save
          </button>
          <button onClick={() => setIsEditing(false)}>Cancel</button>
        </>
      ) : (
        <>
          <h3>{skill?.name}</h3>
          <p>{skill?.description}</p>
          <button onClick={() => setIsEditing(true)}>Edit</button>
        </>
      )}
    </div>
  );
};

// Example 6: Deleting a skill with confirmation
export const SkillWithDelete: React.FC<{ skillId: string }> = ({ skillId }) => {
  const { data: skill, isLoading } = useSkill(skillId);
  const deleteSkill = useDeleteSkill();
  const [showConfirm, setShowConfirm] = React.useState(false);

  const handleDelete = () => {
    deleteSkill.mutate(skillId, {
      onSuccess: () => setShowConfirm(false),
    });
  };

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <h3>{skill?.name}</h3>
      {!showConfirm ? (
        <button onClick={() => setShowConfirm(true)}>Delete</button>
      ) : (
        <div>
          <p>Are you sure?</p>
          <button onClick={handleDelete} disabled={deleteSkill.isPending}>
            Yes, delete
          </button>
          <button onClick={() => setShowConfirm(false)}>Cancel</button>
        </div>
      )}
    </div>
  );
};

// Example 7: Skills with pagination
export const PaginatedSkillsList: React.FC = () => {
  const [page, setPage] = React.useState(1);
  const [limit] = React.useState(10);
  const { data, isLoading } = useSkills({ page, limit });

  return (
    <div>
      {isLoading ? (
        <div>Loading...</div>
      ) : (
        <>
          <div>
            {data?.data.map((skill) => (
              <SkillCard key={skill.id} skill={skill} />
            ))}
          </div>
          <div>
            <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}>
              Previous
            </button>
            <span>Page {page}</span>
            <button
              onClick={() => setPage((p) => (data && p < data.totalPages ? p + 1 : p))}
              disabled={data ? page >= data.totalPages : true}
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
};

// Example 8: Skills with real-time updates via WebSocket
export const RealTimeSkillsList: React.FC = () => {
  const { data, isLoading } = useSkills();
  const [skills, setSkills] = React.useState(data?.data || []);

  React.useEffect(() => {
    if (data?.data) {
      setSkills(data.data);
    }
  }, [data]);

  // This would typically be connected to a WebSocket
  React.useEffect(() => {
    // const ws = new WebSocket('ws://localhost:3000/ws');
    // ws.onmessage = (event) => {
    //   const update = JSON.parse(event.data);
    //   if (update.type === 'skillUpdated') {
    //     setSkills((prev) => prev.map((s) => (s.id === update.id ? update : s)));
    //   }
    // };
  }, []);

  return (
    <div>
      {skills.map((skill) => (
        <SkillCard key={skill.id} skill={skill} />
      ))}
    </div>
  );
};

// Helper component
const SkillCard: React.FC<{ skill: any }> = ({ skill }) => {
  return (
    <div>
      <h3>{skill.name}</h3>
      <p>{skill.description}</p>
      <span>{skill.platform}</span>
      <span>{skill.status}</span>
    </div>
  );
};
