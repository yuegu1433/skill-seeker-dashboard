import React from 'react';
import { useNavigate } from 'react-router-dom';

const CreateSkillPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">创建新技能</h1>
        <p className="mt-1 text-sm text-gray-500">
          通过向导步骤创建您的第一个技能
        </p>
      </div>

      {/* Wizard Steps */}
      <div className="card">
        <div className="card-body">
          <div className="mb-8">
            <nav aria-label="进度" className="relative">
              <ol className="flex items-center justify-between">
                {/* Progress Line */}
                <div className="absolute top-5 left-5 right-5 h-0.5 bg-gray-200 -z-10"></div>

                <li className="relative flex flex-col items-center text-center min-w-0 flex-1">
                  <div className="flex items-center justify-center w-10 h-10 rounded-full bg-primary-600 text-white border-4 border-white shadow-sm">
                    <span className="text-sm font-semibold">1</span>
                  </div>
                  <div className="mt-2 text-sm font-medium text-primary-600 px-2 truncate w-full">
                    基本信息
                  </div>
                </li>

                <li className="relative flex flex-col items-center text-center min-w-0 flex-1">
                  <div className="flex items-center justify-center w-10 h-10 rounded-full bg-gray-300 text-white border-4 border-white shadow-sm">
                    <span className="text-sm font-semibold">2</span>
                  </div>
                  <div className="mt-2 text-sm font-medium text-gray-500 px-2 truncate w-full">
                    源选择
                  </div>
                </li>

                <li className="relative flex flex-col items-center text-center min-w-0 flex-1">
                  <div className="flex items-center justify-center w-10 h-10 rounded-full bg-gray-300 text-white border-4 border-white shadow-sm">
                    <span className="text-sm font-semibold">3</span>
                  </div>
                  <div className="mt-2 text-sm font-medium text-gray-500 px-2 truncate w-full">
                    高级配置
                  </div>
                </li>

                <li className="relative flex flex-col items-center text-center min-w-0 flex-1">
                  <div className="flex items-center justify-center w-10 h-10 rounded-full bg-gray-300 text-white border-4 border-white shadow-sm">
                    <span className="text-sm font-semibold">4</span>
                  </div>
                  <div className="mt-2 text-sm font-medium text-gray-500 px-2 truncate w-full">
                    确认
                  </div>
                </li>
              </ol>
            </nav>
          </div>

          {/* Step Content */}
          <div className="space-y-6">
            <div>
              <label htmlFor="skill-name" className="form-label">
                技能名称
              </label>
              <input
                type="text"
                id="skill-name"
                className="form-input"
                placeholder="输入技能名称"
              />
              <p className="mt-1 text-sm text-gray-500">
                为您的技能起一个有意义的名字
              </p>
            </div>

            <div>
              <label htmlFor="skill-description" className="form-label">
                描述
              </label>
              <textarea
                id="skill-description"
                rows={4}
                className="form-input"
                placeholder="描述这个技能的功能和用途"
              ></textarea>
            </div>

            <div>
              <label className="form-label">平台</label>
              <div className="mt-2 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {['Claude', 'Gemini', 'OpenAI', 'Markdown'].map((platform) => (
                  <div
                    key={platform}
                    className="relative rounded-lg border border-gray-300 bg-white p-4 cursor-pointer hover:border-primary-500 focus:outline-none"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <input
                          id={platform}
                          name="platform"
                          type="radio"
                          className="h-4 w-4 text-primary-600 border-gray-300 focus:ring-primary-500"
                        />
                        <label
                          htmlFor={platform}
                          className="ml-3 block text-sm font-medium text-gray-700"
                        >
                          {platform}
                        </label>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="mt-8 flex justify-end space-x-3">
            <button
              onClick={() => navigate('/skills')}
              className="btn-secondary"
            >
              取消
            </button>
            <button className="btn-primary">下一步</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreateSkillPage;
